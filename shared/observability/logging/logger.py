from __future__ import annotations

import time
from typing import Any

from shared.observability.logging import registry
from shared.observability.logging.context import get_session_id, get_turn_id
from shared.observability.logging.modules import LogModule
from shared.observability.logging.record import LogLevel, LogRecord

# stdlib logging kwargs that GardenLogger does not persist on LogRecord.
_LOGGING_ONLY_KWARGS = frozenset({"exc_info", "stack_info", "stacklevel"})


def _format_message(message: str, args: tuple[Any, ...]) -> str:
    """Support stdlib-style ``logger.info("x=%s", value)`` calls."""
    if not args:
        return message
    try:
        return message % args
    except Exception:
        suffix = " ".join(repr(arg) for arg in args)
        return f"{message} {suffix}"


def _extract_structured_extra(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Map logging-style ``extra={...}`` into Garden structured fields."""
    extra: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key in _LOGGING_ONLY_KWARGS:
            continue
        if key == "extra" and isinstance(value, dict):
            extra.update(value)
        else:
            extra[key] = value
    return extra


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

    def _emit(self, level: LogLevel, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(level, _format_message(message, args), **_extract_structured_extra(kwargs))

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(LogLevel.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(LogLevel.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(LogLevel.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(LogLevel.ERROR, message, *args, **kwargs)


_loggers: dict[LogModule, GardenLogger] = {}


def get_logger(module: LogModule) -> GardenLogger:
    if module not in _loggers:
        _loggers[module] = GardenLogger(module)
    return _loggers[module]
