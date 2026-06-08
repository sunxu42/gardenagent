"""Session → Mem0 动态写入：对话摘要时 / 空闲 N 秒后 / 关停兜底。"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger

from yard.memory.runtime.cold_path import run_memory_cold_path

DEFAULT_MEMORY_FLUSH_IDLE_SEC = 5 * 60
DEFAULT_MEMORY_FLUSH_POLL_SEC = 30.0
DEFAULT_MEMORY_FLUSH_RETRY_DELAY_SEC = 15.0


def _memory_debug(cfg: Any) -> tuple[bool, int]:
    return (
        bool(getattr(cfg, "memory_debug_log_enabled", False)),
        int(getattr(cfg, "memory_debug_log_max_chars", 500) or 500),
    )


def _agent_busy(agent: Any) -> bool:
    q = getattr(agent, "agent_input_queue", None)
    return bool(
        getattr(agent, "_agent_input_processing", False)
        or (q is not None and not q.empty())
    )


def mark_conversation_turn_finished(agent: Any) -> None:
    """记录最近一次非心跳对话轮次结束时间（用于空闲 flush）。"""
    agent._memory_last_turn_finished_at = time.monotonic()


async def flush_agent_session_memory(
    agent: Any,
    *,
    thread_id: str | None = None,
    flush_reason: str = "scheduled",
    flush_journal: bool = False,
) -> None:
    """将 agent 上挂的 session buffer 写入 Mem0（可选仅 flush 单个 thread）。"""
    service = getattr(agent, "mem0_service", None)
    if service is None:
        return
    buffer = getattr(agent, "session_buffer", None)
    if buffer is None:
        return
    if thread_id is None and not buffer.has_pending():
        return

    cfg = getattr(agent, "config", None)
    debug_log_enabled, debug_log_max_chars = _memory_debug(cfg)
    workspace_dir = getattr(cfg, "workspace_dir", "yard/workspace")
    user_id = thread_id

    await run_memory_cold_path(
        service=service,
        buffer=buffer,
        workspace_dir=workspace_dir,
        user_id=user_id,
        flush_session=True,
        flush_journal=flush_journal,
        thread_id=thread_id,
        flush_reason=flush_reason,
        debug_log_enabled=debug_log_enabled,
        debug_log_max_chars=debug_log_max_chars,
    )

    if thread_id is None:
        agent._memory_last_turn_finished_at = None


async def run_memory_idle_flush_loop(
    *,
    agent: Any,
    idle_sec: float = DEFAULT_MEMORY_FLUSH_IDLE_SEC,
    poll_sec: float = DEFAULT_MEMORY_FLUSH_POLL_SEC,
    retry_delay_sec: float = DEFAULT_MEMORY_FLUSH_RETRY_DELAY_SEC,
    stop_event: asyncio.Event | None = None,
) -> None:
    """在「上一轮对话已结束且超过 idle_sec」且 agent 空闲时 flush pending buffer。"""
    local_stop = stop_event or asyncio.Event()

    while not local_stop.is_set():
        try:
            await asyncio.wait_for(local_stop.wait(), timeout=poll_sec)
            return
        except asyncio.TimeoutError:
            pass

        buffer = getattr(agent, "session_buffer", None)
        if buffer is None or not buffer.has_pending():
            continue

        last_finished = getattr(agent, "_memory_last_turn_finished_at", None)
        if last_finished is None:
            continue

        idle_elapsed = time.monotonic() - float(last_finished)
        if idle_elapsed < idle_sec:
            continue

        while not local_stop.is_set() and _agent_busy(agent):
            try:
                await asyncio.wait_for(local_stop.wait(), timeout=retry_delay_sec)
                return
            except asyncio.TimeoutError:
                pass

        if local_stop.is_set():
            return

        try:
            logger.info(
                "Mem0 idle flush triggered ({:.0f}s since last turn)",
                idle_elapsed,
            )
            await flush_agent_session_memory(agent, flush_reason="idle")
        except Exception as e:
            logger.warning("memory idle flush failed: {}", e)
