"""按 emotion taxonomy 渲染 ## Mood 段 + few-shot 段。"""

from __future__ import annotations

from typing import Any

import yaml

DEFAULT_EMOTION = "neutral"


def load_taxonomy(path: str) -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    emotions = data.get("emotions")
    if not isinstance(emotions, dict):
        return {}
    return {str(k): v for k, v in emotions.items() if isinstance(v, dict)}


def _render_few_shot(entry: dict[str, Any]) -> str:
    examples = entry.get("speech_examples")
    if not isinstance(examples, list) or not examples:
        return ""
    blocks = ["## Mood speech examples (few-shot)",
              "Match the tone and pacing of these examples. "
              "Reply in Simplified Chinese unless the user clearly asks for English.", ""]
    for ex in examples:
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


def render_emotion_sections(taxonomy: dict[str, dict[str, Any]], emotion: str) -> str:
    entry = taxonomy.get(emotion) or taxonomy.get(DEFAULT_EMOTION) or {}
    resolved = emotion if emotion in taxonomy else DEFAULT_EMOTION
    label = str(entry.get("label_zh") or resolved).strip()
    guidance = str(entry.get("guidance") or "").strip()

    blocks: list[str] = []
    mood_lines = [f"Current mood: {label} ({resolved})", ""]
    if guidance:
        mood_lines.append(guidance)
    blocks.append("## Mood\n" + "\n".join(mood_lines).strip())

    few_shot = _render_few_shot(entry)
    if few_shot:
        blocks.append(few_shot)
    return "\n\n".join(blocks).strip()
