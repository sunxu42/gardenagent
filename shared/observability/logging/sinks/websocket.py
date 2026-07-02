from __future__ import annotations

import asyncio
from collections import deque
from typing import Awaitable, Callable, Deque

from shared.observability.logging.record import LogLevel, LogRecord

Deliver = Callable[[dict], Awaitable[bool]]


class WebSessionSink:
    """Route session-scoped logs to a single deliver callback (Strategy B lazy flush)."""

    def __init__(self, min_level: LogLevel = LogLevel.INFO, buffer_size: int = 500) -> None:
        self._min = min_level
        self._deliver: Deliver | None = None
        self._buffers: dict[str, Deque[dict]] = {}
        self._buffer_size = buffer_size

    def set_deliver(self, deliver: Deliver) -> None:
        self._deliver = deliver
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        for sid in list(self._buffers.keys()):
            loop.create_task(self._flush_session(sid))

    async def _flush_session(self, session_id: str) -> None:
        if self._deliver is None:
            return
        buf = self._buffers.get(session_id)
        if not buf:
            return
        while buf:
            item = buf[0]
            try:
                delivered = await self._deliver(item)
            except Exception:
                return
            if not delivered:
                return
            buf.popleft()

    async def emit_async(self, record: LogRecord) -> None:
        if record.level.rank() < self._min.rank():
            return
        sid = record.session_id
        if not sid:
            return
        payload = record.to_ws_dict()
        buf = self._buffers.setdefault(sid, deque(maxlen=self._buffer_size))
        buf.append(payload)
        await self._flush_session(sid)

    def emit(self, record: LogRecord) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit_async(record))
        except RuntimeError:
            pass
