from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from yard.observability.logging.paths import dated_filename
from yard.observability.logging.record import LogLevel, LogRecord


class JsonlSink:
    def __init__(self, base_path: Path, min_level: LogLevel = LogLevel.DEBUG) -> None:
        self._base = base_path
        self._min = min_level
        self._current_day: date | None = None
        self._handle = None
        self._base.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_handle(self) -> None:
        today = date.today()
        if self._handle is not None and self._current_day == today:
            return
        if self._handle:
            self._handle.close()
        path = dated_filename(self._base, today)
        self._handle = path.open("a", encoding="utf-8")
        self._current_day = today

    def emit(self, record: LogRecord) -> None:
        if record.level.rank() < self._min.rank():
            return
        self._ensure_handle()
        line = json.dumps(record.sanitize_for_file(), ensure_ascii=False)
        self._handle.write(line + "\n")
        self._handle.flush()

    def close(self) -> None:
        if self._handle:
            self._handle.close()
            self._handle = None
