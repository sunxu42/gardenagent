from __future__ import annotations

import time
from typing import Any

from yard.observability.logging import registry
from yard.observability.logging.context import get_session_id, get_turn_id
from yard.observability.logging.modules import LogModule
from yard.observability.logging.record import LogLevel, LogRecord


class GardenLogger:
    def __init__(self, module: LogModule) -> None:
        self._module = module

    def _log(self, level: LogLevel, message: str, **extra: Any) -> None:
        rec = LogRecord(
            ts_ms=int(time.time() * 1000),
            level=level,
            module=self._module,
            message=message,
            session_id=get_session_id(),
            turn_id=get_turn_id(),
            extra=extra or {},
        )
        registry.dispatch(rec)

    def debug(self, message: str, **extra: Any) -> None:
        self._log(LogLevel.DEBUG, message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        self._log(LogLevel.INFO, message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        self._log(LogLevel.WARNING, message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        self._log(LogLevel.ERROR, message, **extra)


_loggers: dict[LogModule, GardenLogger] = {}


def get_logger(module: LogModule) -> GardenLogger:
    if module not in _loggers:
        _loggers[module] = GardenLogger(module)
    return _loggers[module]
