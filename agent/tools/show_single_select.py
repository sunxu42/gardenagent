"""show_single_select tool：单选 A2UI（variant: default|binary|emoji|cards）。"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.a2ui import render_single_select
from agent.a2ui.prompt import build_tool_description

Variant = Literal["default", "binary", "emoji", "cards"]


class SelectOption(BaseModel):
    id: str = Field(description="选项唯一标识")
    label: str = Field(description="展示文案")
    description: str = Field(default="", description="卡片说明（cards 常用）")
    emoji: str = Field(default="", description="表情（emoji variant 必填）")


class ShowSingleSelectInput(BaseModel):
    title: str = Field(description="卡片标题")
    variant: Variant = Field(description="外观：default|binary|emoji|cards")
    options: list[SelectOption] = Field(description="选项列表")
    description: str = Field(default="", description="可选说明（binary/default）")


_SURFACE = {
    "default": "single-select",
    "binary": "single-select-binary",
    "emoji": "single-select-emoji",
    "cards": "single-select-cards",
}


def create_show_single_select_tool() -> StructuredTool:
    async def show_single_select(
        title: str,
        variant: Variant,
        options: list[SelectOption],
        description: str = "",
    ) -> str:
        cleaned = [
            {
                "id": o.id.strip(),
                "label": o.label.strip(),
                "description": o.description.strip(),
                "emoji": o.emoji.strip(),
            }
            for o in options
            if o.id.strip() and o.label.strip()
        ]
        if not cleaned:
            return json.dumps(
                {"ok": False, "error": "options must be non-empty"},
                ensure_ascii=False,
            )
        if variant == "binary" and len(cleaned) != 2:
            return json.dumps(
                {"ok": False, "error": "binary variant requires exactly 2 options"},
                ensure_ascii=False,
            )
        if variant == "emoji" and any(not o["emoji"] for o in cleaned):
            return json.dumps(
                {"ok": False, "error": "emoji variant requires emoji on every option"},
                ensure_ascii=False,
            )
        try:
            operations = render_single_select(
                title=title.strip(),
                variant=variant,
                options=cleaned,
                description=description.strip(),
            )
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        payload: dict[str, Any] = {
            "a2ui_operations": operations,
            "surface_id": _SURFACE[variant],
        }
        return json.dumps(payload, ensure_ascii=False)

    return StructuredTool.from_function(
        name="show_single_select",
        description=build_tool_description("single_select"),
        coroutine=show_single_select,
        args_schema=ShowSingleSelectInput,
    )
