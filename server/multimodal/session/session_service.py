import asyncio
import json
import uuid

from typing import Any, Callable, Dict, Optional

from agent.events import InputEvent, USER_INPUT_EVENT
from server.agui.bridge import AgUIBridge
from server.agui.interactive import surface_requires_ui_interaction
from server.multimodal.session.backends.factory import SessionBackendFactory
from shared.observability.logging import bind_session, get_logger, set_turn_id
from shared.observability.logging.modules import LogModule

logger = get_logger(LogModule.AGENT)


class SessionService:
    """Bridge WebSocket transport to an agent kernel backend (e.g. AgentManager)."""

    def __init__(self, session_config: dict | None = None):
        self.session_config = session_config or {}

        self.backend = None
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.result_callback: Optional[Callable[[Dict[str, Any]], Any]] = None

        self._read_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None

        self.is_running = False
        self.is_new_session = True

        self.agui_bridge = AgUIBridge()
        self.use_agui_channel = False
        self.agui_message_id: str | None = None
        self.agui_run_id: str | None = None
        self.agui_run_started = False
        self.agui_pending_interaction = False
        self.active_thread_id: str | None = None

    def set_result_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.result_callback = callback

    def current_tts_voice(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "current_tts_voice"):
            return backend.current_tts_voice()
        return None

    def current_tts_emotion(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "current_tts_emotion"):
            return backend.current_tts_emotion()
        return None, 4

    def current_vad_metrics(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "current_vad_metrics"):
            return backend.current_vad_metrics()
        return None

    def baseline_vad(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "baseline_vad"):
            return backend.baseline_vad()
        return None

    def emotion_ui_profile(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "emotion_ui_profile"):
            return backend.emotion_ui_profile()
        return None

    def current_relationship_snapshot(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "current_relationship_snapshot"):
            return backend.current_relationship_snapshot()
        return None

    def vad_snapshot_for_digest(self, digest: str):
        backend = self.backend
        if backend is not None and hasattr(backend, "vad_snapshot_for_digest"):
            return backend.vad_snapshot_for_digest(digest)
        return None

    def end_emotion_turn(self) -> None:
        backend = self.backend
        if backend is not None and hasattr(backend, "end_emotion_turn"):
            backend.end_emotion_turn()

    def affect_settled_metrics(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "affect_settled_metrics"):
            return backend.affect_settled_metrics()
        return None

    def current_tts_prosody(self):
        backend = self.backend
        if backend is not None and hasattr(backend, "current_tts_prosody"):
            return backend.current_tts_prosody()
        return 0, 0, 0

    def set_appraisal_snapshot_listener(self, listener) -> None:
        backend = self.backend
        if backend is not None and hasattr(backend, "set_appraisal_snapshot_listener"):
            backend.set_appraisal_snapshot_listener(listener)

    def clear_affect_locks(self) -> None:
        backend = self.backend
        if backend is not None and hasattr(backend, "clear_affect_locks"):
            backend.clear_affect_locks()

    def set_affect_lock(self, dimension: str, ref_id: str | None) -> dict | None:
        backend = self.backend
        if backend is not None and hasattr(backend, "set_affect_lock"):
            return backend.set_affect_lock(dimension, ref_id)
        return None

    def affect_lock_state(self) -> dict | None:
        backend = self.backend
        if backend is not None and hasattr(backend, "affect_lock_state"):
            return backend.affect_lock_state()
        return None

    def _validate_backend(self) -> None:
        if not hasattr(self.backend, "agent_output_queue"):
            raise RuntimeError("agent_output_queue not found on session backend")
        if not hasattr(self.backend, "agent_input_queue"):
            raise RuntimeError("agent_input_queue not found on session backend")

    def _out_q(self) -> Any:
        self._validate_backend()
        return self.backend.agent_output_queue

    def _in_q(self) -> Any:
        self._validate_backend()
        return self.backend.agent_input_queue

    async def start(self):
        try:
            self.backend = await SessionBackendFactory.async_create_backend(self.session_config)
            self._validate_backend()
            self.is_running = True
            self._read_task = asyncio.create_task(self.read_event())
            self._process_task = asyncio.create_task(self.put_event())
            logger.info("Session 服务已启动")
        except Exception as e:
            logger.error(f"启动 Session 服务失败: {e}")
            raise

    async def stop(self):
        self.is_running = False
        try:
            self.backend.agent_output_queue.put_nowait(None)
        except Exception:
            pass
        try:
            self.queue.put_nowait({"_stop": True})
        except Exception:
            pass

        for t in (self._process_task, self._read_task):
            if t is None:
                continue
            if not t.done():
                t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

        if self.backend is not None and hasattr(self.backend, "aclose"):
            try:
                await self.backend.aclose()
            except Exception as e:
                logger.warning(f"session backend aclose failed: {e}")
        logger.info("Session 服务已停止")

    async def start_session(self):
        self.is_new_session = False

    async def end_session(self):
        self.is_new_session = True

    def begin_agui_turn(self, *, message_id: str, run_id: str) -> None:
        """Enable AG-UI multiplex output for the next assistant run."""
        self.use_agui_channel = True
        self.agui_message_id = message_id
        self.agui_run_id = run_id
        self.agui_run_started = False

    def begin_agui_continuation_turn(self, *, message_id: str) -> str:
        """Start a fresh AG-UI run on an existing assistant message (e.g. after UI action)."""
        run_id = uuid.uuid4().hex
        self.begin_agui_turn(message_id=message_id, run_id=run_id)
        return run_id

    def clear_agui_turn(self) -> None:
        self.use_agui_channel = False
        self.agui_message_id = None
        self.agui_run_id = None
        self.agui_run_started = False
        self.agui_pending_interaction = False

    async def finalize_pending_agui_turn(self) -> None:
        """Force-close a deferred AG-UI run when the user starts a new text turn."""
        if not self.agui_pending_interaction:
            return
        await self._finish_agui_run(force=True)

    async def on_ui_action(
        self,
        event: dict[str, Any],
        *,
        thread_id: str | None = None,
    ) -> bool:
        """Route UI action back into agent input queue as structured user event."""
        normalized = self.agui_bridge.on_ui_action(event)
        if not normalized:
            return False
        run_id = str(normalized.get("runId") or "").strip()
        message_id = str(normalized.get("messageId") or "").strip()
        surface_id = str(normalized.get("surfaceId") or "").strip()
        action = normalized.get("action")
        if not run_id or not message_id or not surface_id or not isinstance(action, dict):
            return False
        in_q = self._in_q()
        payload = {
            "type": "ui_action",
            "run_id": run_id,
            "message_id": message_id,
            "surface_id": surface_id,
            "action": action,
        }
        stable_thread = (
            thread_id.strip()
            if isinstance(thread_id, str) and thread_id.strip()
            else (self.active_thread_id.strip() if isinstance(self.active_thread_id, str) and self.active_thread_id.strip() else None)
        )
        input_event = InputEvent(
            content=json.dumps(payload, ensure_ascii=False),
            event_id=uuid.uuid4().hex,
            event_type=USER_INPUT_EVENT,
            thread_id=stable_thread,
            turn_id=None,
        )
        await self._finish_agui_run(force=True)
        self.begin_agui_continuation_turn(message_id=message_id)
        await in_q.put(input_event)
        return True

    async def _finish_agui_run(self, *, force: bool = False) -> None:
        if self.agui_pending_interaction and not force:
            return
        if not self.use_agui_channel or not self.agui_run_started:
            self.clear_agui_turn()
            return
        message_id = self.agui_message_id
        run_id = self.agui_run_id
        if message_id and run_id:
            await self._publish_agui_envelope(
                self.agui_bridge.run_finished(run_id=run_id, message_id=message_id)
            )
        self.clear_agui_turn()

    async def _publish_agui_envelope(self, envelope: dict) -> None:
        await self.publish_response({"msg_type": "agui", "envelope": envelope})

    async def publish_response(self, message: Dict[str, Any]):
        if self.result_callback is None:
            logger.warning("publish_response: result_callback not set")
            return
        await self.result_callback(message)

    async def read_event(self):
        out_q = self._out_q()
        started: set[str] = set()

        try:
            while self.is_running:
                evt = await out_q.get()
                if evt is None:
                    return
                try:
                    trigger_by = getattr(evt, "trigger_by", None)
                    event_id = getattr(evt, "event_id", None) or getattr(evt, "id", None) or "unknown"
                    phase = getattr(evt, "phase", None) or "middle"
                    data = getattr(evt, "data", None)

                    if trigger_by == "heartbeat":
                        continue

                    if phase == "start":
                        if event_id not in started:
                            await self.publish_response({"msg_type": "SENTENCE_START"})
                            started.add(event_id)
                        continue

                    if phase == "end":
                        if event_id in started:
                            await self.publish_response({"msg_type": "SENTENCE_END"})
                            started.discard(event_id)
                            try:
                                if not started:
                                    await self.end_session()
                                    await self._finish_agui_run()
                            except Exception:
                                pass
                        continue

                    if event_id not in started:
                        await self.publish_response({"msg_type": "SENTENCE_START"})
                        started.add(event_id)

                    if isinstance(data, dict):
                        if "content" in data:
                            content = data.get("content", "")
                            if (
                                self.use_agui_channel
                                and self.agui_message_id
                                and self.agui_run_id
                                and isinstance(content, str)
                            ):
                                if not self.agui_run_started:
                                    await self._publish_agui_envelope(
                                        self.agui_bridge.run_started(
                                            run_id=self.agui_run_id,
                                            message_id=self.agui_message_id,
                                        )
                                    )
                                    self.agui_run_started = True
                                if content:
                                    await self._publish_agui_envelope(
                                        self.agui_bridge.text_delta(
                                            run_id=self.agui_run_id,
                                            message_id=self.agui_message_id,
                                            delta=content,
                                        )
                                    )
                            else:
                                await self.publish_response(
                                    {
                                        "msg_type": "response",
                                        "response": {"role": "assistant", "content": content},
                                    }
                                )
                        elif "a2ui_operations" in data:
                            operations = data.get("a2ui_operations")
                            if (
                                self.use_agui_channel
                                and self.agui_message_id
                                and self.agui_run_id
                                and isinstance(operations, list)
                            ):
                                surface_id = str(data.get("surface_id") or "default-surface").strip()
                                op_list = [item for item in operations if isinstance(item, dict)]
                                if not self.agui_run_started:
                                    await self._publish_agui_envelope(
                                        self.agui_bridge.run_started(
                                            run_id=self.agui_run_id,
                                            message_id=self.agui_message_id,
                                        )
                                    )
                                    self.agui_run_started = True
                                await self._publish_agui_envelope(
                                    self.agui_bridge.a2ui_operations(
                                        run_id=self.agui_run_id,
                                        message_id=self.agui_message_id,
                                        surface_id=surface_id or "default-surface",
                                        operations=op_list,
                                    )
                                )
                                if surface_requires_ui_interaction(surface_id, op_list):
                                    self.agui_pending_interaction = True
                            else:
                                op_count = (
                                    len(operations)
                                    if isinstance(operations, list)
                                    else 0
                                )
                                logger.warning(
                                    "a2ui_operations dropped: AG-UI channel inactive "
                                    "(surface_id=%s, operations=%s)",
                                    data.get("surface_id"),
                                    op_count,
                                )
                        elif "updates" in data:
                            await self.publish_response(
                                {
                                    "msg_type": "response",
                                    "response": {"role": "updates", "updates": data.get("updates", "")},
                                }
                            )
                        else:
                            await self.publish_response(
                                {
                                    "msg_type": "response",
                                    "response": {"role": "assistant", "content": str(data)},
                                }
                            )
                    else:
                        await self.publish_response(
                            {
                                "msg_type": "response",
                                "response": {"role": "assistant", "content": str(data)},
                            }
                        )

                finally:
                    if hasattr(out_q, "task_done"):
                        out_q.task_done()

        except asyncio.CancelledError:
            logger.info("read_event: cancelled")
        except Exception as e:
            logger.error(f"read_event: loop failed: {e}")

    async def put_event(self):
        while self.is_running:
            in_q = self._in_q()
            message = await self.queue.get()
            if not message:
                continue
            if isinstance(message, dict) and message.get("_stop") is True:
                return

            text = message.get("text", "")
            is_final = message.get("is_final", False)

            if not text:
                continue

            if not is_final:
                continue

            if self.is_new_session:
                await self.start_session()

            thread_id = message.get("thread_id")
            if isinstance(thread_id, str) and thread_id.strip():
                tid = thread_id.strip()
                self.active_thread_id = tid
            else:
                tid = None

            turn_id = message.get("turn_id")
            turn = turn_id.strip() if isinstance(turn_id, str) and turn_id.strip() else None

            session = tid or "default"
            with bind_session(session):
                if turn:
                    set_turn_id(turn)
                input_event = InputEvent(
                    content=text,
                    event_id=uuid.uuid4().hex,
                    event_type=USER_INPUT_EVENT,
                    thread_id=tid,
                    turn_id=turn,
                )
                await in_q.put(input_event)
