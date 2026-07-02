import asyncio
import uuid
from typing import Any
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

from agent.events import InputEvent, HEARTBEAT_INPUT_EVENT
from agent.memory.runtime.cold_path import add_daily_journal_if_present
from shared.config.paths import DEFAULT_WORKSPACE_DIR

HeartbeatPrompt = """Periodic heartbeat tick. Do not call tools or infer tasks from prior chats. If no explicit pending task is already available in current context, reply exactly HEARTBEAT_OK."""

DEFAULT_INTERVAL_SEC = 30 * 60
DEFAULT_RETRY_DELAY_SEC = 60.0


def build_heartbeat_input_event(prompt: str | None = None, thread_id: str | None = None) -> InputEvent:
    text = prompt if prompt is not None else HeartbeatPrompt
    return InputEvent(
        content=text,
        event_id=uuid.uuid4().hex,
        event_type=HEARTBEAT_INPUT_EVENT,
        thread_id=thread_id,
    )


async def run_heartbeat_enqueue_loop(
    *,
    agent: Any,
    interval_sec: float = DEFAULT_INTERVAL_SEC,
    retry_delay_sec: float = DEFAULT_RETRY_DELAY_SEC,
    prompt: str | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Timer loop: put heartbeat events on ``agent.agent_input_queue`` when idle."""
    local_stop = stop_event or asyncio.Event()
    q = agent.agent_input_queue

    def _busy() -> bool:
        return bool(
            getattr(agent, "_agent_input_processing", False)
            or not q.empty()
        )

    while not local_stop.is_set():
        scheduler = getattr(agent, "local_scheduler", None)
        if scheduler is not None:
            try:
                consumed = await scheduler.consume_pending_wake()
            except Exception as e:
                _log.error(f"consume pending wake failed: {e}")
                consumed = False
            if consumed:
                _log.info("consumed pending wake before heartbeat interval")

        try:
            await asyncio.wait_for(local_stop.wait(), timeout=interval_sec)
            return
        except asyncio.TimeoutError:
            pass

        while not local_stop.is_set() and _busy():
            _log.debug(f"heartbeat deferred: input queue or worker busy, retry in {retry_delay_sec}s")
            try:
                await asyncio.wait_for(local_stop.wait(), timeout=retry_delay_sec)
                return
            except asyncio.TimeoutError:
                pass

        if local_stop.is_set():
            return
        if _busy():
            continue

        cfg = getattr(agent, "config", None)
        if cfg and getattr(cfg, "memory_enabled", False) and getattr(
            cfg, "memory_journal_on_heartbeat", True
        ):
            service = getattr(agent, "mem0_service", None)
            workspace_dir = getattr(cfg, "workspace_dir", DEFAULT_WORKSPACE_DIR)
            debug_log_enabled = bool(getattr(cfg, "memory_debug_log_enabled", False))
            debug_log_max_chars = int(getattr(cfg, "memory_debug_log_max_chars", 500) or 500)
            try:
                await add_daily_journal_if_present(
                    service,
                    workspace_dir,
                    user_id=getattr(cfg, "mem0_user_id", None),
                    debug_log_enabled=debug_log_enabled,
                    debug_log_max_chars=debug_log_max_chars,
                )
            except Exception as e:
                _log.warning(f"memory journal heartbeat failed: {e}")

        try:
            heartbeat_thread_id = getattr(agent, "_last_user_thread_id", None)
            if not (isinstance(heartbeat_thread_id, str) and heartbeat_thread_id.strip()):
                cfg_tid = getattr(getattr(agent, "config", None), "mem0_user_id", None)
                heartbeat_thread_id = cfg_tid if isinstance(cfg_tid, str) and cfg_tid.strip() else "default"
            await q.put(build_heartbeat_input_event(prompt, thread_id=heartbeat_thread_id))
            _log.info("heartbeat enqueued on agent input queue")
        except Exception as e:
            _log.error(f"heartbeat enqueue failed: {e}")
