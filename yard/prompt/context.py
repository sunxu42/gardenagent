"""当轮 Prompt 上下文。"""

from __future__ import annotations

from dataclasses import dataclass

from yard.emotion.core.policy import ResponsePolicy


@dataclass
class PromptContext:
    agent_emotion: str = "neutral"
    emotion_scale: int = 4
    response_policy: ResponsePolicy | None = None
    user_emotion_label: str | None = None
    affective_v2_enabled: bool = False
    trust: float = 0.5
    warmth: float = 0.4
    relationship_stage: str = "acquaintance"
    interpersonal_cue: str = ""
    turn_type: str = "neutral"
    has_memories: bool = False
    memory_bullets: str = ""
    locale: str = "zh"
    user_v: float = 0.0
    empathy_mode: str = "neutral"

    def get(self, name: str):
        return getattr(self, name, None)
