"""Extract text from chat messages (last user turn / system flatten)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage


def last_human_text(messages: list[Any]) -> str:
    """Return the most recent human/user message text, or empty string."""
    for msg in reversed(messages):
        role = getattr(msg, "type", None)
        if role is None and isinstance(msg, dict):
            role = msg.get("role")
        if role not in ("human", "user"):
            continue
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content", "")
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return "\n".join(parts).strip()
        return str(content or "").strip()
    return ""


def flatten_system_text(system_message: SystemMessage | None) -> str:
    """Flatten a SystemMessage into a single string."""
    if system_message is None:
        return ""
    content = system_message.content
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    for block in system_message.content_blocks:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "\n".join(parts).strip()
