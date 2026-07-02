"""Garden unified logging — public API."""

from shared.observability.logging import config as logging_config
from shared.observability.logging.context import (
    bind_session,
    get_session_id,
    get_turn_id,
    set_turn_id,
)
from shared.observability.logging.logger import GardenLogger, get_logger
from shared.observability.logging.modules import LogModule, module_color, module_short_name
from shared.observability.logging.record import LogLevel, LogRecord
from shared.observability.logging import registry
from shared.observability.logging.paths import resolve_log_file
from shared.observability.logging.sinks.console import ConsoleSink
from shared.observability.logging.sinks.jsonl import JsonlSink
from shared.observability.logging.sinks.websocket import WebSessionSink

_web_sink: WebSessionSink | None = None


def configure_logging() -> WebSessionSink:
    global _web_sink
    registry.clear_sinks()
    if logging_config.LOG_CONSOLE_ENABLED:
        registry.register_sink(
            ConsoleSink(min_level=LogLevel(logging_config.LOG_LEVEL))
        )
    if logging_config.LOG_FILE_ENABLED:
        path = resolve_log_file(logging_config.LOG_DIR, logging_config.LOG_FILE)
        registry.register_sink(
            JsonlSink(path, min_level=LogLevel(logging_config.LOG_FILE_LEVEL))
        )
    _web_sink = WebSessionSink(
        min_level=LogLevel.INFO,
        buffer_size=logging_config.LOG_UI_BUFFER_SIZE,
    )
    if logging_config.LOG_WEBSOCKET_ENABLED:
        registry.register_sink(_web_sink)
    get_logger(LogModule.SYSTEM).info("GardenLogger configured")
    return _web_sink


def get_web_session_sink() -> WebSessionSink | None:
    return _web_sink


def set_session_log_deliver(deliver) -> None:
    if _web_sink:
        _web_sink.set_deliver(deliver)


__all__ = [
    "GardenLogger",
    "LogLevel",
    "LogModule",
    "LogRecord",
    "bind_session",
    "configure_logging",
    "get_logger",
    "get_session_id",
    "get_turn_id",
    "get_web_session_sink",
    "module_color",
    "module_short_name",
    "set_session_log_deliver",
    "set_turn_id",
]
