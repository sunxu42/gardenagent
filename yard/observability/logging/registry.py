from __future__ import annotations

import sys
from typing import Protocol

from yard.observability.logging.record import LogRecord


class LogSink(Protocol):
    def emit(self, record: LogRecord) -> None: ...


_sinks: list[LogSink] = []


def register_sink(sink: LogSink) -> None:
    _sinks.append(sink)


def clear_sinks() -> None:
    _sinks.clear()


def dispatch(record: LogRecord) -> None:
    for sink in _sinks:
        try:
            sink.emit(record)
        except Exception as exc:
            print(f"[GardenLogger] sink failed: {exc!r}", file=sys.stderr)
