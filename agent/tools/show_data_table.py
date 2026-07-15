"""show_data_table tool：渲染只读或可点选行的 A2UI 表格。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from agent.a2ui import render_data_table
from agent.a2ui.prompt import build_tool_description


class TableColumn(BaseModel):
    key: str = Field(description="列字段 key，需与 rows 中字段对应")
    header: str = Field(description="列标题")


class TableRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(description="行唯一标识，interactive=true 时用于回传")


def create_show_data_table_tool() -> StructuredTool:
    class ShowDataTableInput(BaseModel):
        title: str = Field(description="表格标题")
        columns: list[TableColumn] = Field(description="列定义，建议 2-4 列")
        rows: list[TableRow] = Field(description="行数据，每行含 id 及各列字段")
        interactive: bool = Field(
            default=False,
            description="true 时用户需点击选择一行；false 时只读展示对比",
        )
        footnote: str = Field(default="", description="可选脚注")

    async def show_data_table(
        title: str,
        columns: list[TableColumn] | None = None,
        rows: list[TableRow] | None = None,
        interactive: bool = False,
        footnote: str = "",
    ) -> str:
        column_items = columns or []
        row_items = rows or []
        if not column_items:
            return json.dumps({"ok": False, "error": "columns 不能为空"}, ensure_ascii=False)
        if not row_items:
            return json.dumps({"ok": False, "error": "rows 不能为空"}, ensure_ascii=False)

        normalized_columns = [
            {"key": item.key.strip(), "header": item.header.strip()}
            for item in column_items
            if item.key.strip() and item.header.strip()
        ]
        normalized_rows: list[dict[str, str]] = []
        for index, row in enumerate(row_items):
            row_data = row.model_dump()
            row_id = str(row_data.pop("id", "") or f"row-{index + 1}").strip()
            normalized_rows.append({"id": row_id, **{k: str(v) for k, v in row_data.items()}})

        try:
            operations = render_data_table(
                normalized_columns,
                normalized_rows,
                title=title.strip() or "对比",
                interactive=interactive,
                footnote=footnote,
            )
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

        surface_id = "data-table-select" if interactive else "data-table"
        payload: dict[str, Any] = {
            "a2ui_operations": operations,
            "surface_id": surface_id,
        }
        return json.dumps(payload, ensure_ascii=False)

    return StructuredTool.from_function(
        name="show_data_table",
        description=build_tool_description("data_table"),
        coroutine=show_data_table,
        args_schema=ShowDataTableInput,
    )
