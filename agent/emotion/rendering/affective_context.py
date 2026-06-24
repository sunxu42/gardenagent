"""渲染 ## User state 与 ## Relationship 段。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent.emotion.core.relationship import derive_stage
from agent.emotion.rendering.taxonomy import DEFAULT_EMOTION, load_taxonomy
from agent.emotion.synthesis.strategy_tags import StrategyTags, strategy_tags_summary
from shared.config.paths import DEFAULT_PROMPTS_DIR

_DEFAULT_AFFECTIVE_FILENAME = "affective.yaml"


def _default_affective_path(affective_path: str | None = None) -> str:
    if affective_path:
        return affective_path
    return str(Path(DEFAULT_PROMPTS_DIR) / _DEFAULT_AFFECTIVE_FILENAME)


def _load_affective(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def render_user_state_section(
    *,
    affective_path: str,
    user_emotion_label: str,
) -> str:
    user_states = load_taxonomy(affective_path)
    user_entry = user_states.get(user_emotion_label) or user_states.get(DEFAULT_EMOTION) or {}
    user_label = str(user_entry.get("label_zh") or user_emotion_label).strip()
    empathy = str(user_entry.get("empathy_guidance") or "").strip()
    user_lines = [f"感知：用户情绪倾向为 {user_label}（{user_emotion_label}）。"]
    if empathy:
        user_lines.append(f"共情策略：{empathy}")
    return "## User state\n" + "\n".join(user_lines).strip()


def render_relationship_section(
    *,
    affective_path: str,
    trust: float,
    warmth: float,
    interpersonal_cue: str,
) -> str:
    data = _load_affective(affective_path)
    stages_raw = data.get("stages")
    stages = (
        {str(k): v for k, v in stages_raw.items() if isinstance(v, dict)}
        if isinstance(stages_raw, dict)
        else {}
    )
    stage = derive_stage(trust, warmth)
    stage_entry = stages.get(stage) or {}
    stage_label = str(stage_entry.get("label_zh") or stage).strip()
    interaction = str(stage_entry.get("interaction_guidance") or "").strip()
    rel_lines = [f"关系阶段：{stage_label}（信任 {trust:.2f} / 亲近 {warmth:.2f}）。"]
    cue = (interpersonal_cue or "").strip()
    if cue:
        rel_lines.append(f"本轮态度：{cue}")
    if interaction:
        rel_lines.append(f"互动策略：{interaction}")
    return "## Relationship\n" + "\n".join(rel_lines).strip()


def render_strategy_section(tags: StrategyTags | None) -> str:
    if tags is None:
        return ""
    summary = strategy_tags_summary(tags)
    lines = [
        "## Strategy",
        f"Tags: mode={tags.mode}, voice={tags.voice_style}, length={tags.length}, tts={tags.tts_profile}",
    ]
    if summary:
        lines.append(f"Summary: {summary}")
    if tags.llm_guideline:
        lines.append(f"Hard constraints: {tags.llm_guideline}")
    return "\n".join(lines).strip()


def render_affective_sections(
    *,
    affective_path: str,
    user_emotion_label: str,
    trust: float,
    warmth: float,
    interpersonal_cue: str,
) -> str:
    path = _default_affective_path(affective_path)
    blocks = [
        render_user_state_section(
            affective_path=path,
            user_emotion_label=user_emotion_label,
        ),
        render_relationship_section(
            affective_path=path,
            trust=trust,
            warmth=warmth,
            interpersonal_cue=interpersonal_cue,
        ),
    ]
    return "\n\n".join(b for b in blocks if b).strip()
