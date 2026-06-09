"""将 YAML slice 值格式化为 prompt 文本。"""

from __future__ import annotations

from typing import Any


def format_slice_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        if not value:
            return ""
        if isinstance(value[0], dict):
            return format_dialogue_examples(value)
        lines = [str(x).strip() for x in value if str(x).strip()]
        if not lines:
            return ""
        return "\n".join(f"- {line}" for line in lines)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items() if v is not None)
    return str(value).strip()


def format_dialogue_examples(examples: list[dict], *, limit: int | None = None) -> str:
    blocks: list[str] = []
    items = examples[:limit] if limit else examples
    for ex in items:
        if not isinstance(ex, dict):
            continue
        user = str(ex.get("user") or "").strip()
        assistant = str(ex.get("assistant") or "").strip()
        if not user or not assistant:
            continue
        blocks.append(f"User: {user}")
        blocks.append(f"Assistant: {assistant}")
        blocks.append("")
    return "\n".join(blocks).strip()
