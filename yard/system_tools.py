from __future__ import annotations

from calendar import c
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.tools import StructuredTool

DEFAULT_TIMEZONE = ZoneInfo("Asia/Shanghai")


def create_session_status_tool() -> StructuredTool:
    async def session_status(
        sessionKey: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        # Parameters are accepted for forward compatibility.
        del sessionKey, model
        now = datetime.now(DEFAULT_TIMEZONE)
        card = f"🕒 {now:%Y-%m-%d %H:%M}\n"
        card += f"Timezone: {DEFAULT_TIMEZONE}\n"
        return card

    return StructuredTool.from_function(
        name="session_status",
        description=(
            "Show a /status-equivalent session status card (usage + time + cost when available). "
            "Use for model-use questions (📊 session_status). Optional: set per-session model override "
            "(model=default resets overrides). Can be called without parameters."
        ),
        coroutine=session_status,
    )
