from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from yard.observability.logging.modules import LogModule, module_short_name

_FILE_STRIP_EXTRA_KEYS = frozenset({"raw_text", "audio_path", "audio_data"})


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    def rank(self) -> int:
        return {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}[self.value]


@dataclass
class LogRecord:
    ts_ms: int
    level: LogLevel
    module: LogModule
    message: str
    session_id: str | None = None
    turn_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def format_time(self) -> str:
        dt = datetime.fromtimestamp(self.ts_ms / 1000, tz=timezone.utc).astimezone()
        return dt.strftime("%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"

    def format_line(self) -> str:
        short = module_short_name(self.module)
        return f"{self.format_time()}  {short:<3}  {self.message}"

    def to_ws_dict(self) -> dict[str, Any]:
        return {
            "type": "log_entry",
            "schema_version": 1,
            "ts_ms": self.ts_ms,
            "level": self.level.value,
            "module": self.module.value,
            "message": self.message,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "extra": self.extra or None,
        }

    def sanitize_for_file(self) -> dict[str, Any]:
        extra = dict(self.extra) if self.extra else {}
        for key in _FILE_STRIP_EXTRA_KEYS:
            extra.pop(key, None)
        return {
            "ts_ms": self.ts_ms,
            "level": self.level.value,
            "module": self.module.value,
            "message": self.message,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "extra": extra or None,
        }
