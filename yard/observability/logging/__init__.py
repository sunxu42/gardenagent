"""Garden unified logging — public API."""

from yard.observability.logging.config import LoggingConfig
from yard.observability.logging.context import (
    bind_session,
    get_session_id,
    get_turn_id,
    set_turn_id,
)
from yard.observability.logging.logger import GardenLogger, get_logger
from yard.observability.logging.modules import LogModule, module_color, module_short_name
from yard.observability.logging.record import LogLevel, LogRecord
from yard.observability.logging import registry
from yard.observability.logging.paths import resolve_log_file
from yard.observability.logging.sinks.console import ConsoleSink
from yard.observability.logging.sinks.jsonl import JsonlSink
from yard.observability.logging.sinks.websocket import WebSessionSink

_web_sink: WebSessionSink | None = None


def configure_logging(cfg: LoggingConfig) -> WebSessionSink:
    global _web_sink
    registry.clear_sinks()
    if cfg.console:
        registry.register_sink(ConsoleSink(min_level=LogLevel(cfg.level)))
    if cfg.file_enabled:
        path = resolve_log_file(cfg.dir, cfg.file)
        registry.register_sink(JsonlSink(path, min_level=LogLevel(cfg.file_level)))
    _web_sink = WebSessionSink(
        min_level=LogLevel.INFO,
        buffer_size=cfg.ui_buffer_size,
    )
    if cfg.websocket:
        registry.register_sink(_web_sink)
    get_logger(LogModule.SYSTEM).info("GardenLogger configured")
    return _web_sink


def get_web_session_sink() -> WebSessionSink | None:
    return _web_sink


def register_session_emitter(session_id: str, emitter) -> None:
    if _web_sink:
        _web_sink.register(session_id, emitter)


def unregister_session_emitter(session_id: str) -> None:
    if _web_sink:
        _web_sink.unregister(session_id)


__all__ = [
    "GardenLogger",
    "LogLevel",
    "LogModule",
    "LogRecord",
    "LoggingConfig",
    "bind_session",
    "configure_logging",
    "get_logger",
    "get_session_id",
    "get_turn_id",
    "get_web_session_sink",
    "module_color",
    "module_short_name",
    "register_session_emitter",
    "set_turn_id",
    "unregister_session_emitter",
]
