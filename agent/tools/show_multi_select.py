"""show_multi_select tool：渲染多选 A2UI 卡片。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.a2ui import render_multi_select
from agent.a2ui.prompt import build_tool_description


class SelectOption(BaseModel):
    id: str = Field(description="选项唯一标识")
    label: str = Field(description="展示文案")
    description: str = Field(default="", description="可选副标题")


class ShowMultiSelectInput(BaseModel):
    title: str = Field(description="卡片标题")
    options: list[SelectOption] = Field(description="可勾选项，至少 1 项")
    confirm_label: str = Field(default="确认选择", description="确认按钮文案")


def create_show_multi_select_tool() -> StructuredTool:
    async def show_multi_select(
        title: str,
        options: list[SelectOption] | None = None,
        confirm_label: str = "确认选择",
    ) -> str:
        items = options or []
        if not items:
            return json.dumps({"ok": False, "error": "options 不能为空"}, ensure_ascii=False)

        normalized = [
            {
                "id": item.id.strip(),
                "label": item.label.strip(),
                **({"description": item.description.strip()} if item.description.strip() else {}),
            }
            for item in items
        ]
        operations = render_multi_select(
            normalized,
            title=title.strip(),
            confirm_label=confirm_label.strip() or "确认选择",
        )
        payload: dict[str, Any] = {
            "a2ui_operations": operations,
            "surface_id": "multi-select",
        }
        return json.dumps(payload, ensure_ascii=False)

    return StructuredTool.from_function(
        name="show_multi_select",
        description=build_tool_description("multi_select"),
        coroutine=show_multi_select,
        args_schema=ShowMultiSelectInput,
    )
