"""Flatten system message text for prompt composer and middleware."""

from __future__ import annotations

from langchain_core.messages import SystemMessage

__all__ = ["flatten_system_text"]


def flatten_system_text(system_message: SystemMessage | None) -> str:
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
