"""show_date_picker tool：渲染年月日选择 A2UI 卡片。"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.a2ui import render_date_picker
from agent.a2ui.prompt import build_tool_description

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _parse_optional_date(value: str, field: str) -> tuple[str | None, str | None]:
    text = value.strip()
    if not text:
        return "", None
    match = _DATE_RE.match(text)
    if not match:
        return "", f"{field} 必须是 YYYY-MM-DD 格式"
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        date(year, month, day)
    except ValueError:
        return "", f"{field} 不是有效日期"
    return text, None


class ShowDatePickerInput(BaseModel):
    title: str = Field(description="卡片标题")
    description: str = Field(default="", description="可选说明文字")
    min_date: str = Field(default="", description="可选最早日期，格式 YYYY-MM-DD")
    max_date: str = Field(default="", description="可选最晚日期，格式 YYYY-MM-DD")
    default_date: str = Field(default="", description="可选默认日期，格式 YYYY-MM-DD；留空则前端用当天")
    confirm_label: str = Field(default="确认日期", description="确认按钮文案")


def create_show_date_picker_tool() -> StructuredTool:
    async def show_date_picker(
        title: str,
        description: str = "",
        min_date: str = "",
        max_date: str = "",
        default_date: str = "",
        confirm_label: str = "确认日期",
    ) -> str:
        normalized_min, min_error = _parse_optional_date(min_date, "min_date")
        if min_error:
            return json.dumps({"ok": False, "error": min_error}, ensure_ascii=False)

        normalized_max, max_error = _parse_optional_date(max_date, "max_date")
        if max_error:
            return json.dumps({"ok": False, "error": max_error}, ensure_ascii=False)

        normalized_default, default_error = _parse_optional_date(default_date, "default_date")
        if default_error:
            return json.dumps({"ok": False, "error": default_error}, ensure_ascii=False)

        if normalized_min and normalized_max and normalized_min > normalized_max:
            return json.dumps(
                {"ok": False, "error": "min_date 不能晚于 max_date"},
                ensure_ascii=False,
            )

        if normalized_default:
            if normalized_min and normalized_default < normalized_min:
                return json.dumps(
                    {"ok": False, "error": "default_date 早于 min_date"},
                    ensure_ascii=False,
                )
            if normalized_max and normalized_default > normalized_max:
                return json.dumps(
                    {"ok": False, "error": "default_date 晚于 max_date"},
                    ensure_ascii=False,
                )

        operations = render_date_picker(
            title=title.strip() or "请选择日期",
            description=description.strip(),
            min_date=normalized_min,
            max_date=normalized_max,
            default_date=normalized_default,
            confirm_label=confirm_label.strip() or "确认日期",
        )
        payload: dict[str, Any] = {
            "a2ui_operations": operations,
            "surface_id": "date-picker",
        }
        return json.dumps(payload, ensure_ascii=False)

    return StructuredTool.from_function(
        name="show_date_picker",
        description=build_tool_description("date_picker"),
        coroutine=show_date_picker,
        args_schema=ShowDatePickerInput,
    )
