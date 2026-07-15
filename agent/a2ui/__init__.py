"""A2UI fixed-schema helpers for agent tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

A2UI_VERSION = "v0.9"
DEFAULT_CATALOG_ID = "shadcn"
SINGLE_SELECT_SURFACE_ID = "single-select"
SINGLE_SELECT_BINARY_SURFACE_ID = "single-select-binary"
SINGLE_SELECT_EMOJI_SURFACE_ID = "single-select-emoji"
SINGLE_SELECT_CARDS_SURFACE_ID = "single-select-cards"
MULTI_SELECT_SURFACE_ID = "multi-select"
DATA_TABLE_SURFACE_ID = "data-table"
DATA_TABLE_SELECT_SURFACE_ID = "data-table-select"
DATE_PICKER_SURFACE_ID = "date-picker"
_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    """Load a fixed A2UI schema JSON by name."""
    path = _SCHEMAS_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def render_plan_selector(
    plans: list[dict[str, str]],
    *,
    surface_id: str = SINGLE_SELECT_CARDS_SURFACE_ID,
    title: str = "请选择方案",
) -> list[dict[str, Any]]:
    """Build A2UI v0.9 operations for a card-style single-select list."""
    plan_children: list[str] = []
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": ["title", "plan-list"]},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
        {"id": "plan-list", "component": "Column", "children": plan_children},
    ]

    for index, plan in enumerate(plans):
        plan_id = (plan.get("id") or f"plan-{index + 1}").strip()
        label = (plan.get("label") or plan_id).strip()
        description = (plan.get("description") or "").strip()
        card_id = f"plan-{plan_id}"
        plan_children.append(card_id)
        card: dict[str, Any] = {
            "id": card_id,
            "component": "PlanOptionCard",
            "planId": plan_id,
            "title": label,
            "action": {
                "event": {
                    "name": "confirm_plan",
                    "context": {"planId": plan_id},
                }
            },
        }
        if description:
            card["description"] = description
        components.append(card)

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": DEFAULT_CATALOG_ID,
            },
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components,
            },
        },
        {
            "version": A2UI_VERSION,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/selectedPlan",
                "value": None,
            },
        },
    ]


def render_single_select_default(
    options: list[dict[str, str]],
    *,
    title: str,
    description: str = "",
    surface_id: str = SINGLE_SELECT_SURFACE_ID,
) -> list[dict[str, Any]]:
    """Build a plain list single-select surface."""
    root_children: list[str] = ["title"]
    option_children: list[str] = []
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": root_children},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
    ]
    if description.strip():
        root_children.append("desc")
        components.append(
            {
                "id": "desc",
                "component": "Text",
                "text": description.strip(),
                "variant": "body",
            }
        )
    root_children.append("option-list")
    components.append({"id": "option-list", "component": "Column", "children": option_children})

    for index, option in enumerate(options):
        option_id = (option.get("id") or f"option-{index + 1}").strip()
        label = (option.get("label") or option_id).strip()
        node_id = f"option-{option_id}"
        option_children.append(node_id)
        components.append(
            {
                "id": node_id,
                "component": "SingleSelectOption",
                "optionId": option_id,
                "label": label,
                "action": {
                    "event": {
                        "name": "confirm_option",
                        "context": {"optionId": option_id},
                    }
                },
            }
        )

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {"surfaceId": surface_id, "catalogId": DEFAULT_CATALOG_ID},
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
        {
            "version": A2UI_VERSION,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/selectedOption",
                "value": None,
            },
        },
    ]


def render_single_select(
    *,
    title: str,
    variant: str,
    options: list[dict[str, str]],
    description: str = "",
) -> list[dict[str, Any]]:
    """Dispatch single-select rendering by explicit UI variant."""
    normalized = variant.strip().lower()
    if normalized == "binary":
        if len(options) != 2:
            raise ValueError("binary variant requires exactly 2 options")
        return render_binary_choice(
            title=title,
            option_a=options[0],
            option_b=options[1],
            description=description,
            surface_id=SINGLE_SELECT_BINARY_SURFACE_ID,
        )
    if normalized == "emoji":
        return render_emoji_picker(
            options,
            title=title,
            surface_id=SINGLE_SELECT_EMOJI_SURFACE_ID,
        )
    if normalized == "cards":
        return render_plan_selector(
            plans=options,
            title=title,
            surface_id=SINGLE_SELECT_CARDS_SURFACE_ID,
        )
    if normalized == "default":
        return render_single_select_default(
            options,
            title=title,
            description=description,
            surface_id=SINGLE_SELECT_SURFACE_ID,
        )
    raise ValueError(f"unknown single_select variant: {variant}")


def render_multi_select(
    options: list[dict[str, str]],
    *,
    title: str,
    surface_id: str = MULTI_SELECT_SURFACE_ID,
    confirm_label: str = "确认选择",
) -> list[dict[str, Any]]:
    """Build A2UI v0.9 operations for a multi-select card."""
    option_children: list[str] = []
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": ["title", "option-list", "confirm-btn"]},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
        {"id": "option-list", "component": "Column", "children": option_children},
        {
            "id": "confirm-btn",
            "component": "MultiSelectConfirmButton",
            "text": confirm_label,
            "action": {"event": {"name": "confirm_selection"}},
        },
    ]

    for index, option in enumerate(options):
        option_id = (option.get("id") or f"option-{index + 1}").strip()
        label = (option.get("label") or option_id).strip()
        description = (option.get("description") or "").strip()
        node_id = f"option-{option_id}"
        option_children.append(node_id)
        node: dict[str, Any] = {
            "id": node_id,
            "component": "MultiSelectOption",
            "optionId": option_id,
            "label": label,
        }
        if description:
            node["description"] = description
        components.append(node)

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {"surfaceId": surface_id, "catalogId": DEFAULT_CATALOG_ID},
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
        {
            "version": A2UI_VERSION,
            "updateDataModel": {"surfaceId": surface_id, "path": "/selectedIds", "value": []},
        },
    ]


def render_binary_choice(
    *,
    title: str,
    option_a: dict[str, str],
    option_b: dict[str, str],
    description: str = "",
    surface_id: str = SINGLE_SELECT_BINARY_SURFACE_ID,
) -> list[dict[str, Any]]:
    """Build A2UI v0.9 operations for a two-button single-select card."""
    root_children = ["title"]
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": root_children},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
    ]
    if description.strip():
        root_children.append("desc")
        components.append(
            {"id": "desc", "component": "Text", "text": description.strip(), "variant": "body"}
        )
    root_children.append("choices")
    components.append(
        {"id": "choices", "component": "Row", "children": ["choice-a", "choice-b"]}
    )

    for suffix, option, variant in (
        ("a", option_a, "primary"),
        ("b", option_b, "secondary"),
    ):
        choice_id = option["id"].strip()
        components.append(
            {
                "id": f"choice-{suffix}",
                "component": "BinaryChoiceButton",
                "choiceId": choice_id,
                "label": option["label"].strip(),
                "variant": variant,
                "action": {
                    "event": {
                        "name": "confirm_choice",
                        "context": {"choiceId": choice_id},
                    }
                },
            }
        )

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {"surfaceId": surface_id, "catalogId": DEFAULT_CATALOG_ID},
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
    ]


def render_emoji_picker(
    options: list[dict[str, str]],
    *,
    title: str,
    surface_id: str = SINGLE_SELECT_EMOJI_SURFACE_ID,
) -> list[dict[str, Any]]:
    """Build A2UI v0.9 operations for an emoji single-select card."""
    option_children: list[str] = []
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": ["title", "option-list"]},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
        {"id": "option-list", "component": "Column", "children": option_children},
    ]

    for index, option in enumerate(options):
        option_id = (option.get("id") or f"emoji-{index + 1}").strip()
        emoji = (option.get("emoji") or "").strip()
        label = (option.get("label") or option_id).strip()
        node_id = f"emoji-{option_id}"
        option_children.append(node_id)
        components.append(
            {
                "id": node_id,
                "component": "EmojiOption",
                "optionId": option_id,
                "emoji": emoji,
                "label": label,
                "action": {
                    "event": {
                        "name": "confirm_emoji",
                        "context": {"optionId": option_id, "emoji": emoji},
                    }
                },
            }
        )

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {"surfaceId": surface_id, "catalogId": DEFAULT_CATALOG_ID},
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
        {
            "version": A2UI_VERSION,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/selectedEmoji",
                "value": None,
            },
        },
    ]


def render_data_table(
    columns: list[dict[str, str]],
    rows: list[dict[str, str]],
    *,
    title: str,
    interactive: bool = False,
    footnote: str = "",
    surface_id: str | None = None,
) -> list[dict[str, Any]]:
    """Build a read-only or row-selectable data table surface."""
    normalized_columns = [
        {
            "key": (column.get("key") or "").strip(),
            "header": (column.get("header") or column.get("key") or "").strip(),
        }
        for column in columns
        if (column.get("key") or "").strip()
    ]
    if not normalized_columns:
        raise ValueError("columns 不能为空")

    normalized_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        row_id = (row.get("id") or f"row-{index + 1}").strip()
        cells = {
            column["key"]: str(row.get(column["key"], "")).strip()
            for column in normalized_columns
        }
        normalized_rows.append({"id": row_id, **cells})

    if not normalized_rows:
        raise ValueError("rows 不能为空")

    resolved_surface_id = surface_id or (
        DATA_TABLE_SELECT_SURFACE_ID if interactive else DATA_TABLE_SURFACE_ID
    )
    column_keys = [column["key"] for column in normalized_columns]
    root_children: list[str] = ["title"]
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": root_children},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
    ]

    if interactive:
        root_children.append("table-shell")
        components.append(
            {
                "id": "table-shell",
                "component": "Column",
                "children": ["col-header", "row-list"],
                "gap": "sm",
            }
        )
        row_children: list[str] = []
        components.append(
            {
                "id": "col-header",
                "component": "DataTableColumnHeader",
                "columns": normalized_columns,
            }
        )
        components.append({"id": "row-list", "component": "Column", "children": row_children})
        for row in normalized_rows:
            row_id = row["id"]
            node_id = f"row-{row_id}"
            row_children.append(node_id)
            cells = {key: row.get(key, "") for key in column_keys}
            components.append(
                {
                    "id": node_id,
                    "component": "DataTableRowOption",
                    "rowId": row_id,
                    "columnKeys": column_keys,
                    "columns": normalized_columns,
                    "cells": cells,
                    "action": {
                        "event": {
                            "name": "confirm_row",
                            "context": {"rowId": row_id, "cells": cells},
                        }
                    },
                }
            )
        operations: list[dict[str, Any]] = [
            {
                "version": A2UI_VERSION,
                "createSurface": {
                    "surfaceId": resolved_surface_id,
                    "catalogId": DEFAULT_CATALOG_ID,
                },
            },
            {
                "version": A2UI_VERSION,
                "updateComponents": {
                    "surfaceId": resolved_surface_id,
                    "components": components,
                },
            },
            {
                "version": A2UI_VERSION,
                "updateDataModel": {
                    "surfaceId": resolved_surface_id,
                    "path": "/selectedRow",
                    "value": None,
                },
            },
        ]
    else:
        root_children.append("table")
        table_rows = [{key: row.get(key, "") for key in column_keys} for row in normalized_rows]
        components.append(
            {
                "id": "table",
                "component": "DataTable",
                "columns": normalized_columns,
                "data": table_rows,
            }
        )
        operations = [
            {
                "version": A2UI_VERSION,
                "createSurface": {
                    "surfaceId": resolved_surface_id,
                    "catalogId": DEFAULT_CATALOG_ID,
                },
            },
            {
                "version": A2UI_VERSION,
                "updateComponents": {
                    "surfaceId": resolved_surface_id,
                    "components": components,
                },
            },
        ]

    if footnote.strip():
        root_children.append("footnote")
        components.append(
            {
                "id": "footnote",
                "component": "Text",
                "text": footnote.strip(),
                "variant": "caption",
                "tone": "muted",
            }
        )

    return operations


def render_date_picker(
    *,
    title: str,
    description: str = "",
    min_date: str = "",
    max_date: str = "",
    default_date: str = "",
    confirm_label: str = "确认日期",
    surface_id: str = DATE_PICKER_SURFACE_ID,
) -> list[dict[str, Any]]:
    """Build A2UI v0.9 operations for a year/month/day date picker card."""
    root_children: list[str] = ["title"]
    components: list[dict[str, Any]] = [
        {"id": "root", "component": "Card", "children": root_children},
        {"id": "title", "component": "Text", "text": title, "variant": "h3"},
    ]

    if description.strip():
        root_children.append("desc")
        components.append(
            {"id": "desc", "component": "Text", "text": description.strip(), "variant": "body"}
        )

    root_children.append("picker")
    picker: dict[str, Any] = {
        "id": "picker",
        "component": "DatePicker",
        "confirmLabel": confirm_label.strip() or "确认日期",
        "action": {"event": {"name": "confirm_date"}},
    }
    if min_date.strip():
        picker["minDate"] = min_date.strip()
    if max_date.strip():
        picker["maxDate"] = max_date.strip()
    if default_date.strip():
        picker["defaultDate"] = default_date.strip()
    components.append(picker)

    return [
        {
            "version": A2UI_VERSION,
            "createSurface": {"surfaceId": surface_id, "catalogId": DEFAULT_CATALOG_ID},
        },
        {
            "version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
        {
            "version": A2UI_VERSION,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/selectedDate",
                "value": None,
            },
        },
    ]
