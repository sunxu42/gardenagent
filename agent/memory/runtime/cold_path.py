"""心跳冷路径：session buffer flush + 可选日记 add。"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from agent.observability.logging import LogModule, get_logger
from agent.observability.logging.turn_log import log_memory_event

_log = get_logger(LogModule.SYSTEM)

from agent.memory.mem0.service import Mem0Service
from agent.memory.core.filters import has_memory_value
from agent.memory.core.buffer import SessionBuffer


def _truncate(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if max_chars <= 0:
        return ""
    return t if len(t) <= max_chars else (t[: max_chars - 1] + "…")


async def flush_session_buffer_to_mem0(
    service: Mem0Service,
    buffer: SessionBuffer,
    *,
    user_id: str | None = None,
    thread_id: str | None = None,
    flush_reason: str = "session_flush",
    debug_log_enabled: bool = False,
    debug_log_max_chars: int = 500,
) -> int:
    """将 session buffer 批量 add 到 Mem0；可指定 thread_id 仅 flush 单会话。返回 flush 的 thread 数。"""
    if thread_id:
        messages = buffer.flush_thread(thread_id)
        batches = {thread_id: messages} if messages else {}
    else:
        batches = buffer.flush_all()
    count = 0
    for tid, messages in batches.items():
        uid = user_id or tid or service.default_user_id
        if not messages:
            continue
        if not has_memory_value(messages):
            _log.debug(
                f"Mem0 session_flush skipped (no memory value) thread={tid} messages={len(messages)}",
            )
            continue
        try:
            if debug_log_enabled:
                joined = "\n".join(
                    f"{m.get('role')}: {m.get('content', '')}" for m in messages if isinstance(m, dict)
                )
                _log.info(
                    f"[mem0:add:session_flush] reason={flush_reason} thread={tid} "
                    f"embedding_input(messages): {_truncate(joined, debug_log_max_chars)}",
                )
            await service.aadd(
                messages,
                user_id=uid,
                metadata={"source": "session_flush", "flush_reason": flush_reason, "thread_id": tid},
                infer=True,
            )
            count += 1
            log_memory_event(
                f"memory flush · {flush_reason} · {len(messages)} messages",
                action="flush",
                flush_reason=flush_reason,
                thread_id=tid,
                message_count=len(messages),
            )
        except Exception as e:
            _log.warning(f"Mem0 session_flush failed (thread={tid}): {e}")
    return count


async def add_daily_journal_if_present(
    service: Mem0Service,
    workspace_dir: str | Path,
    *,
    user_id: str | None = None,
    day: date | None = None,
    debug_log_enabled: bool = False,
    debug_log_max_chars: int = 500,
) -> bool:
    """若存在 memory/YYYY-MM-DD.md，作为额外 infer add 输入。"""
    root = Path(workspace_dir)
    d = day or date.today()
    journal = root / "memory" / f"{d.isoformat()}.md"
    if not journal.is_file():
        return False
    try:
        content = journal.read_text(encoding="utf-8").strip()
        if not content:
            return False
        if debug_log_enabled:
            _log.info(
                f"[mem0:add:daily_journal] embedding_input(user): {_truncate(content, debug_log_max_chars)}",
            )
        await service.aadd(
            [{"role": "user", "content": content}],
            user_id=user_id,
            metadata={"source": "heartbeat", "category": "episodic"},
            infer=True,
        )
        _log.debug(f"Mem0 heartbeat journal add: {journal.name}")
        return True
    except Exception as e:
        _log.warning(f"Mem0 journal add failed: {e}")
        return False


async def run_memory_cold_path(
    *,
    service: Mem0Service | None,
    buffer: SessionBuffer | None,
    workspace_dir: str,
    user_id: str | None = None,
    flush_session: bool = True,
    flush_journal: bool = True,
    thread_id: str | None = None,
    flush_reason: str = "cold_path",
    debug_log_enabled: bool = False,
    debug_log_max_chars: int = 500,
) -> None:
    if service is None:
        return
    if flush_session and buffer is not None:
        await flush_session_buffer_to_mem0(
            service,
            buffer,
            user_id=user_id,
            thread_id=thread_id,
            flush_reason=flush_reason,
            debug_log_enabled=debug_log_enabled,
            debug_log_max_chars=debug_log_max_chars,
        )
    if flush_journal:
        await add_daily_journal_if_present(
            service,
            workspace_dir,
            user_id=user_id,
            debug_log_enabled=debug_log_enabled,
            debug_log_max_chars=debug_log_max_chars,
        )
