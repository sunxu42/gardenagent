def _apply_langchain_reviver_explicit_default() -> None:
    """langgraph's jsonplus sets LC_REVIVER = Reviver() at import; avoid pending deprecation."""
    from langchain_core.load.load import Reviver

    _orig = Reviver.__init__

    def __init__(self, allowed_objects=None, *args, **kwargs):
        if allowed_objects is None:
            allowed_objects = "core"
        return _orig(self, allowed_objects, *args, **kwargs)

    Reviver.__init__ = __init__  # type: ignore[method-assign]


_apply_langchain_reviver_explicit_default()

import asyncio
from typing import Any

import yaml

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AIMessageChunk

from yard.events import HEARTBEAT_INPUT_EVENT, InputEvent, OutputEvent
from yard.middlewares import PersonaPromptMiddleware
from yard.middlewares.persona_prompt_middleware import resolve_soul_profile
from yard.graph import create_deep_agent
from yard.configs.resolve import resolve_yard_runtime
from yard.configs.secrets import load_secrets
from yard.configs.settings import load_settings
from yard.init_workspace import init_workspace
from yard.heartbeat import run_heartbeat_enqueue_loop
from yard.memory.runtime.flush import mark_conversation_turn_finished
from yard.memory.bootstrap import (
    setup_memory_subsystem,
    start_memory_background_tasks,
    shutdown_memory_subsystem,
)
from yard.emotion.bootstrap import setup_emotion_subsystem
from yard.timer import LocalSchedulerService, create_cron_tool
from yard.system_tools import create_session_status_tool
from yard.observability.logging import LogModule, bind_session, get_logger, set_turn_id

_log = get_logger(LogModule.AGENT)

from yard.observability.langfuse_safe import init_langfuse, safe_flush


def create_glm_model(config):
    model = ChatOpenAI(
        model=config.llm_model_name,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        temperature=0.7,
        max_tokens=20000,
        streaming=True,
        extra_body={
            "thinking": {"type": "disabled"},
        },
    )
    return model


async def load_mcp_tools(config):
    with open(config.mcp_servers_yaml, encoding="utf-8") as f:
        mcp_servers_config = yaml.safe_load(f)
    try:
        mcp_client = MultiServerMCPClient(mcp_servers_config)
    except Exception as e:
        raise e

    all_tools = []
    for name in mcp_client.connections.keys():
        try:
            tools = await mcp_client.get_tools(server_name=name)
        except Exception as e:
            print(f"[warn] MCP server '{name}' is unavailable and will be skipped")
            continue
        all_tools.extend(tools)
    return all_tools


def load_subagents(config_path) -> list:
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    available_tools = {}
    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        if "model" in spec:
            subagent["model"] = spec["model"]
        if "tools" in spec:
            avt = []
            for t in spec["tools"]:
                if t in available_tools:
                    avt.append(available_tools[t])

            subagent["tools"] = avt
        subagents.append(subagent)

    return subagents


def _apply_subsystem(yard_manager, emotion, memory) -> None:
    """将 emotion / memory 子系统装配结果挂到 YardManager 实例。"""
    yard_manager.emotion_service = emotion.service
    yard_manager.emotion_appraisal_middleware = emotion.appraisal_middleware
    yard_manager.tts_voice_type = emotion.tts_voice_type
    yard_manager.mem0_service = memory.mem0_service
    yard_manager.session_buffer = memory.session_buffer


class YardManager:

    def __init__(self, config=None):
        settings = load_settings(config)
        secrets = load_secrets()
        self.config = resolve_yard_runtime(settings, secrets)
        self.langfuse_client, self.langfuse_handler = init_langfuse()

    @classmethod
    async def create(cls, config=None):
        yard_manager = cls(config)
        init_workspace(yard_manager.config.workspace_dir)

        yard_manager.tools = await load_mcp_tools(yard_manager.config)
        yard_manager.local_scheduler = LocalSchedulerService(agent=yard_manager)
        yard_manager.local_scheduler.start()
        yard_manager.tools.append(create_cron_tool(yard_manager.local_scheduler))
        yard_manager.tools.append(create_session_status_tool())

        backend = FilesystemBackend(
            root_dir=yard_manager.config.workspace_dir,
            virtual_mode=True,
        )

        emotion = setup_emotion_subsystem(yard_manager.config)
        memory = setup_memory_subsystem(yard_manager.config, yard_manager)
        _apply_subsystem(yard_manager, emotion, memory)

        from yard.prompt.bootstrap import setup_prompt_composer

        cfg = yard_manager.config
        composer = setup_prompt_composer(cfg, emotion_service=emotion.service)
        composer_on = bool(getattr(cfg, "prompt_composer_enabled", False))

        middleware: list[Any] = []
        middleware.extend(memory.middleware)
        middleware.extend(emotion.appraisal_middleware)
        if composer is not None:
            middleware.append(composer)
        if not composer_on:
            middleware.append(PersonaPromptMiddleware(cfg.prompts_dir))
            middleware.extend(emotion.prompt_middleware)
        yard_manager.tools.extend(memory.extra_tools)

        yard_manager._checkpointer = MemorySaver()
        yard_manager.agent = create_deep_agent(
            model=create_glm_model(yard_manager.config),
            tools=yard_manager.tools,
            system_prompt=None,
            skills=[yard_manager.config.skills_dir],
            backend=backend,
            checkpointer=yard_manager._checkpointer,
            middleware=middleware,
        )

        from yard.memory.admin.user_data import register_yard_manager

        register_yard_manager(yard_manager)

        yard_manager.agent_input_queue = asyncio.Queue(maxsize=1000)
        yard_manager.agent_output_queue = asyncio.Queue(maxsize=1000)
        yard_manager._agent_input_processing = False

        yard_manager._worker_stop = asyncio.Event()
        yard_manager._worker_task = asyncio.create_task(
            yard_manager._agent_input_worker(),
            name="input_worker",
        )
        yard_manager._heartbeat_stop = asyncio.Event()
        yard_manager._heartbeat_task = asyncio.create_task(
            run_heartbeat_enqueue_loop(
                agent=yard_manager,
                stop_event=yard_manager._heartbeat_stop,
            ),
            name="heartbeat_enqueue",
        )
        start_memory_background_tasks(yard_manager)
        return yard_manager

    def current_tts_voice(self):
        """每次从 soul.yaml 读取 voice_type（与 prompt 热更新一致）。"""
        try:
            voice = resolve_soul_profile(self.config.prompts_dir).get("voice_type")
            if voice and str(voice).strip():
                return str(voice).strip()
        except Exception as e:
            _log.debug(f"解析 TTS 音色失败，使用缓存: {e}")
        return getattr(self, "tts_voice_type", None)

    def current_tts_emotion(self):
        """返回 (emotion, emotion_scale)；优先策略层 TTS preset，否则用 VAD 投影。"""
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None, 4
        syn = svc.last_synthesis()
        if syn is not None:
            act = syn.actuation
            emotion = (act.tts_emotion or "").strip() or None
            if emotion and emotion != "neutral":
                return emotion, int(act.tts_emotion_scale)
        emotion, scale = svc.last_render
        return emotion, scale

    def current_vad_metrics(self):
        """返回最近一轮 appraisal 结果与当前 agent VAD。"""
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        try:
            current = svc.current().as_dict()
            target = (
                svc.last_appraisal_target.as_dict()
                if svc.last_appraisal_target is not None
                else dict(current)
            )
            return {
                "utterance_vad": target,
                "agent_vad_after": current,
                "weight": svc.last_appraisal_weight,
            }
        except Exception:
            return None

    def baseline_vad(self):
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        try:
            return svc.baseline().as_dict()
        except Exception:
            return None

    def emotion_ui_profile(self):
        """供前端说明栏展示：双端 baseline 与衰减参数。"""
        try:
            from yard.emotion.constants import (
                EMOTION_ALPHA,
                EMOTION_BETA,
                EMOTION_REL_ALPHA,
                EMOTION_REL_TAU_SEC,
                EMOTION_TAU_SEC,
                USER_AFFECT_NEUTRAL_A,
                USER_AFFECT_NEUTRAL_D,
                USER_AFFECT_NEUTRAL_V,
            )
            from yard.middlewares.persona_prompt_middleware import resolve_soul_profile

            prof = resolve_soul_profile(self.config.prompts_dir)
            soul_base = prof.get("baseline") or {}
            rel_base = prof.get("relationship_baseline") or {}
            svc = getattr(self, "emotion_service", None)
            if svc is not None:
                agent_vad = svc.baseline().as_dict()
            else:
                agent_vad = {
                    "v": float(soul_base.get("v", 0.0)),
                    "a": float(soul_base.get("a", 0.3)),
                    "d": float(soul_base.get("d", 0.0)),
                }
            return {
                "user_vad_baseline": {
                    "v": USER_AFFECT_NEUTRAL_V,
                    "a": USER_AFFECT_NEUTRAL_A,
                    "d": USER_AFFECT_NEUTRAL_D,
                },
                "agent_vad_baseline": agent_vad,
                "relationship_baseline": {
                    "trust": float(rel_base.get("trust", 0.5)),
                    "warmth": float(rel_base.get("warmth", 0.4)),
                },
                "user_affect": {
                    "per_turn_only": True,
                },
                "agent_vad": {
                    "per_turn_alpha": EMOTION_ALPHA,
                    "per_turn_beta": EMOTION_BETA,
                    "time_tau_sec": EMOTION_TAU_SEC,
                },
                "relationship": {
                    "per_turn_alpha": EMOTION_REL_ALPHA,
                    "time_tau_sec": EMOTION_REL_TAU_SEC,
                },
            }
        except Exception:
            return None

    def current_relationship_snapshot(self):
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        try:
            from yard.emotion.core.relationship import derive_stage

            rel = svc.relationship()
            return {
                "trust": rel.trust,
                "warmth": rel.warmth,
                "stage": derive_stage(rel.trust, rel.warmth),
            }
        except Exception:
            return None

    def vad_snapshot_for_digest(self, digest: str):
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        try:
            return svc.get_appraisal_snapshot(digest)
        except Exception:
            return None

    def end_emotion_turn(self) -> None:
        svc = getattr(self, "emotion_service", None)
        if svc is not None and hasattr(svc, "end_turn"):
            svc.end_turn()

    def reset_emotion_state(self) -> bool:
        """将情绪子系统恢复为人设 baseline（清空用户数据时调用）。"""
        svc = getattr(self, "emotion_service", None)
        if svc is None or not hasattr(svc, "reset_to_defaults"):
            return False
        try:
            svc.reset_to_defaults()
        except Exception as e:
            _log.warning(f"reset_emotion_state failed: {e!r}")
            return False
        for mw in getattr(self, "emotion_appraisal_middleware", ()) or ():
            reset_fn = getattr(mw, "reset_session_state", None)
            if callable(reset_fn):
                try:
                    reset_fn()
                except Exception as e:
                    _log.warning(f"emotion appraisal middleware reset failed: {e!r}")
        return True

    def affect_settled_metrics(self):
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        try:
            return svc.build_settled_metrics()
        except Exception:
            return None

    def current_tts_prosody(self):
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return 0, 0, 0
        syn = svc.last_synthesis()
        if syn is None:
            return 0, 0, 0
        act = syn.actuation
        return (
            int(act.speech_rate),
            int(act.pitch),
            int(getattr(act, "loudness_rate", 0) or 0),
        )

    def set_appraisal_snapshot_listener(self, listener) -> None:
        svc = getattr(self, "emotion_service", None)
        if svc is not None and hasattr(svc, "set_appraisal_snapshot_listener"):
            svc.set_appraisal_snapshot_listener(listener)

    def clear_affect_locks(self) -> None:
        svc = getattr(self, "emotion_service", None)
        if svc is not None and hasattr(svc, "clear_affect_locks"):
            svc.clear_affect_locks()

    def set_affect_lock(self, dimension: str, ref_id: str | None) -> dict | None:
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        svc.set_affect_lock(dimension, ref_id)
        return svc.lock_state()

    def affect_lock_state(self) -> dict | None:
        svc = getattr(self, "emotion_service", None)
        if svc is None:
            return None
        return svc.lock_state()

    async def aclose(self) -> None:
        """Stop background worker and heartbeat task."""
        local_scheduler = getattr(self, "local_scheduler", None)
        if local_scheduler is not None:
            await local_scheduler.shutdown()

        await shutdown_memory_subsystem(self)

        worker_stop = getattr(self, "_worker_stop", None)
        hb_stop = getattr(self, "_heartbeat_stop", None)
        if worker_stop is not None:
            worker_stop.set()
        if hb_stop is not None:
            hb_stop.set()

        worker_task = getattr(self, "_worker_task", None)
        hb_task = getattr(self, "_heartbeat_task", None)
        if worker_task is not None and not worker_task.done():
            worker_task.cancel()
        if hb_task is not None and not hb_task.done():
            hb_task.cancel()

        for task in (worker_task, hb_task):
            if task is None:
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def achat(self, user_input: str, thread_id="yard-manager-demo"):
        stream_config = {"configurable": {"thread_id": thread_id}}
        if self.langfuse_handler is not None:
            stream_config["callbacks"] = [self.langfuse_handler]
            stream_config["metadata"] = {
                "langfuse_session_id": thread_id,
                "langfuse_tags": ["yard-manager"],
            }
        async for chunk, _ in self.agent.astream(
            {"messages": [("user", user_input)]},
            config=stream_config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    yield {"content": chunk.content}
                if chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        name = tool_call.get("name", "unknown")
                        args = tool_call.get("args", {})
                        if name == "read_file":
                            file_path = args.get("path", "")
                            yield {"updates": f">> 读取文件: {file_path}"}
                        else:
                            yield {"updates": f">> 调用工具: {name}"}

            elif isinstance(chunk, ToolMessage):
                name = chunk.name

                yield {"updates": f"{name}调用工具结束"}

    async def astream(self, event: InputEvent):
        event_id = event.event_id
        trigger_by = event.event_type

        self.agent_output_queue.put_nowait(
            OutputEvent(data={}, trigger_by=trigger_by, event_id=event_id, phase="start")
        )

        try:
            stable = getattr(event, "thread_id", None)
            thread_id = (
                stable.strip()
                if isinstance(stable, str) and stable.strip()
                else (str(event_id) if event_id else "yard-manager-demo")
            )
            if trigger_by != HEARTBEAT_INPUT_EVENT:
                self._last_user_thread_id = thread_id
            turn_id = getattr(event, "turn_id", None)
            turn = turn_id.strip() if isinstance(turn_id, str) and turn_id.strip() else None
            with bind_session(thread_id, turn_id=turn):
                async for chunk in self.achat(event.content, thread_id=thread_id):
                    self.agent_output_queue.put_nowait(
                        OutputEvent(data=chunk, trigger_by=trigger_by, event_id=event_id, phase="middle")
                    )

                self.agent_output_queue.put_nowait(
                    OutputEvent(data={}, trigger_by=trigger_by, event_id=event_id, phase="end")
                )

            if trigger_by != HEARTBEAT_INPUT_EVENT and self.mem0_service is not None:
                mark_conversation_turn_finished(self)
        finally:
            safe_flush(self.langfuse_client)

    async def _agent_input_worker(self) -> None:
        while not self._worker_stop.is_set():
            if self._agent_input_processing:
                await asyncio.sleep(0.1)
                continue
            try:
                item = await self.agent_input_queue.get()
                self._agent_input_processing = True
                try:
                    await self.astream(item)
                finally:
                    self._agent_input_processing = False
                    self.agent_input_queue.task_done()
            except asyncio.CancelledError:
                return
