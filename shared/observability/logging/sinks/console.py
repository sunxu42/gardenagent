from __future__ import annotations

import sys

from shared.observability.logging.modules import module_color, module_short_name
from shared.observability.logging.record import LogLevel, LogRecord

_LEVEL_COLORS = {
    LogLevel.DEBUG: "\033[90m",
    LogLevel.INFO: "\033[32m",
    LogLevel.WARNING: "\033[33m",
    LogLevel.ERROR: "\033[31m",
}
_RESET = "\033[0m"


class ConsoleSink:
    def __init__(self, min_level: LogLevel = LogLevel.INFO) -> None:
        self._min = min_level

    def emit(self, record: LogRecord) -> None:
        if record.level.rank() < self._min.rank():
            return
        mod_color = _hex_to_ansi(module_color(record.module))
        short = module_short_name(record.module)
        lvl_color = _LEVEL_COLORS.get(record.level, "")
        line = record.format_line()
        parts = line.split(f"  {short}  ", 1)
        if len(parts) == 2:
            out = f"{parts[0]}  {mod_color}[{short}]{_RESET}  {lvl_color}{parts[1]}{_RESET}"
        else:
            out = f"{lvl_color}{line}{_RESET}"
        print(out, file=sys.stdout, flush=True)


def _hex_to_ansi(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
