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
import os
import yaml

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AIMessageChunk

from yard.events import HEARTBEAT_INPUT_EVENT, InputEvent, OutputEvent
from yard.middlewares import PersonaPromptMiddleware
from yard.graph import create_deep_agent
from yard.configs.config import load_config
from yard.init_workspace import init_workspace
from yard.heartbeat import run_heartbeat_enqueue_loop
from yard.memory.runtime.flush import mark_conversation_turn_finished
from yard.memory.bootstrap import (
    setup_memory_subsystem,
    start_memory_background_tasks,
    shutdown_memory_subsystem,
)
from yard.timer import LocalSchedulerService, create_cron_tool
from yard.system_tools import create_session_status_tool
from langfuse import get_client
from langfuse.langchain import CallbackHandler


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


def _apply_memory_subsystem(yard_manager, memory) -> None:
    yard_manager.mem0_service = memory.mem0_service
    yard_manager.session_buffer = memory.session_buffer


class YardManager:

    def __init__(self, config=None):
        self.config = load_config(config)
        self.langfuse_client = self._init_langfuse_client()
        self.langfuse_handler = self._init_langfuse_handler()

    def _langfuse_enabled(self):
        return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

    def _init_langfuse_client(self):
        if not self._langfuse_enabled():
            return None
        try:
            return get_client()
        except Exception:
            return None

    def _init_langfuse_handler(self):
        if not self._langfuse_enabled():
            return None
        try:
            return CallbackHandler()
        except Exception:
            return None

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

        memory = setup_memory_subsystem(yard_manager.config, yard_manager)
        _apply_memory_subsystem(yard_manager, memory)

        middleware = [PersonaPromptMiddleware(yard_manager.config.prompts_dir)]
        middleware.extend(memory.middleware)
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
            if self.langfuse_client is not None:
                try:
                    self.langfuse_client.flush()
                except Exception:
                    pass

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
