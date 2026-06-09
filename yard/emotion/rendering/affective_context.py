"""渲染 ## User state 与 ## Relationship 段。"""

from __future__ import annotations

from typing import Any

import yaml

from yard.emotion.core.policy import ResponsePolicy
from yard.emotion.core.relationship import derive_stage
from yard.emotion.rendering.taxonomy import DEFAULT_EMOTION, load_taxonomy


def _load_stages(path: str) -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    stages = data.get("stages")
    if not isinstance(stages, dict):
        return {}
    return {str(k): v for k, v in stages.items() if isinstance(v, dict)}


def render_user_state_section(
    *,
    user_states_path: str,
    user_emotion_label: str,
) -> str:
    user_states = load_taxonomy(user_states_path)
    user_entry = user_states.get(user_emotion_label) or user_states.get(DEFAULT_EMOTION) or {}
    user_label = str(user_entry.get("label_zh") or user_emotion_label).strip()
    empathy = str(user_entry.get("empathy_guidance") or "").strip()
    user_lines = [f"感知：用户情绪倾向为 {user_label}（{user_emotion_label}）。"]
    if empathy:
        user_lines.append(f"共情策略：{empathy}")
    return "## User state\n" + "\n".join(user_lines).strip()


def render_relationship_section(
    *,
    relationship_stages_path: str,
    trust: float,
    warmth: float,
    interpersonal_cue: str,
    response_policy: ResponsePolicy | None,
) -> str:
    stages = _load_stages(relationship_stages_path)
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
    if response_policy is not None:
        if response_policy.repair_action != "none":
            rel_lines.append(f"修复策略：{response_policy.repair_action}")
        rel_lines.append(f"表达直接度：{response_policy.directiveness:.2f}")
    return "## Relationship\n" + "\n".join(rel_lines).strip()


def render_affective_sections(
    *,
    user_states_path: str,
    relationship_stages_path: str,
    user_emotion_label: str,
    trust: float,
    warmth: float,
    interpersonal_cue: str,
    response_policy: ResponsePolicy | None,
) -> str:
    blocks = [
        render_user_state_section(
            user_states_path=user_states_path,
            user_emotion_label=user_emotion_label,
        ),
        render_relationship_section(
            relationship_stages_path=relationship_stages_path,
            trust=trust,
            warmth=warmth,
            interpersonal_cue=interpersonal_cue,
            response_policy=response_policy,
        ),
    ]
    return "\n\n".join(blocks).strip()
