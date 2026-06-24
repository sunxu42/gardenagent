from __future__ import annotations

import asyncio
from collections import deque
from typing import Awaitable, Callable, Deque

from shared.observability.logging.record import LogLevel, LogRecord

Emitter = Callable[[dict], Awaitable[None]]


class WebSessionSink:
    def __init__(self, min_level: LogLevel = LogLevel.INFO, buffer_size: int = 500) -> None:
        self._min = min_level
        self._emitters: dict[str, Emitter] = {}
        self._buffers: dict[str, Deque[dict]] = {}
        self._buffer_size = buffer_size

    def register(self, session_id: str, emitter: Emitter) -> None:
        self._emitters[session_id] = emitter
        buf = self._buffers.setdefault(session_id, deque(maxlen=self._buffer_size))
        for item in buf:
            asyncio.create_task(emitter(item))

    def unregister(self, session_id: str) -> None:
        self._emitters.pop(session_id, None)

    async def emit_async(self, record: LogRecord) -> None:
        if record.level.rank() < self._min.rank():
            return
        sid = record.session_id
        if not sid:
            return
        payload = record.to_ws_dict()
        buf = self._buffers.setdefault(sid, deque(maxlen=self._buffer_size))
        buf.append(payload)
        emitter = self._emitters.get(sid)
        if emitter:
            await emitter(payload)

    def emit(self, record: LogRecord) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit_async(record))
        except RuntimeError:
            pass
