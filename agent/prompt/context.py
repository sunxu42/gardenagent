"""Prompt context for the current model turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agent.emotion.core.policy import ResponsePolicy

if TYPE_CHECKING:
    from agent.emotion.synthesis.strategy_tags import StrategyTags
    from agent.prompt.reply_plan import ReplyPlan


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
    strategy_tags: "StrategyTags | None" = None
    reply_plan: ReplyPlan | None = None

    def get(self, name: str):
        return getattr(self, name, None)
