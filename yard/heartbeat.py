import asyncio
import uuid
from typing import Any
from loguru import logger

from yard.events import InputEvent, HEARTBEAT_INPUT_EVENT

HeartbeatPrompt = """Periodic heartbeat tick. Do not call tools or infer tasks from prior chats. If no explicit pending task is already available in current context, reply exactly HEARTBEAT_OK."""

DEFAULT_INTERVAL_SEC = 30 * 60
DEFAULT_RETRY_DELAY_SEC = 60.0


def build_heartbeat_input_event(prompt: str | None = None) -> InputEvent:
    text = prompt if prompt is not None else HeartbeatPrompt
    return InputEvent(content=text, event_id=uuid.uuid4().hex, event_type=HEARTBEAT_INPUT_EVENT)


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
                logger.error("consume pending wake failed: {}", e)
                consumed = False
            if consumed:
                logger.info("consumed pending wake before heartbeat interval")

        try:
            await asyncio.wait_for(local_stop.wait(), timeout=interval_sec)
            return
        except asyncio.TimeoutError:
            pass

        while not local_stop.is_set() and _busy():
            logger.debug("heartbeat deferred: input queue or worker busy, retry in %ss", retry_delay_sec)
            try:
                await asyncio.wait_for(local_stop.wait(), timeout=retry_delay_sec)
                return
            except asyncio.TimeoutError:
                pass

        if local_stop.is_set():
            return
        if _busy():
            continue

        try:
            await q.put(build_heartbeat_input_event(prompt))
            logger.info("heartbeat enqueued on agent input queue")
        except Exception as e:
            logger.error("heartbeat enqueue failed: {}", e)
