"""Build PromptContext from ModelRequest and EmotionService."""

from __future__ import annotations

from typing import Any, Callable

from langchain.agents.middleware.types import ModelRequest

from yard.emotion.core.relationship import derive_stage
from yard.emotion.core.service import EmotionService
from yard.prompt.context import PromptContext
from yard.prompt.reply_plan import DanhuangReplyPlanner


def infer_turn_type(ctx: PromptContext) -> str:
    cue = (ctx.interpersonal_cue or "").strip()
    for kw in ("\u9a82", "\u6307\u8d23", "\u4fae\u8fb1", "\u5a01\u80c1"):
        if kw in cue:
            return "crisis"
    if ctx.emotion_scale >= 2 or abs(ctx.user_v) > 0.5:
        return "emotional"
    return "neutral"


class PromptContextBuilder:
    def __init__(
        self,
        *,
        config: Any,
        emotion_service: EmotionService | None,
        mem0_format_fn: Callable[[list], str],
    ) -> None:
        self._config = config
        self._emotion_service = emotion_service
        self._mem0_format = mem0_format_fn
        self._reply_planner = DanhuangReplyPlanner()

    def build(self, request: ModelRequest) -> PromptContext:
        emotion, scale = "neutral", 4
        svc = self._emotion_service
        if svc is not None:
            emotion, scale = svc.snapshot_for_turn()

        rel = svc.relationship() if svc is not None else None
        memories = request.state.get("mem0_memories") or []
        bullets = ""
        if memories:
            try:
                bullets = self._mem0_format(memories)
            except Exception:
                bullets = ""

        user_v = float(getattr(svc, "last_user_v", 0.0) or 0.0) if svc is not None else 0.0

        policy = getattr(svc, "last_response_policy", None) if svc else None
        empathy_mode = policy.empathy_mode if policy is not None else "neutral"

        ctx = PromptContext(
            agent_emotion=emotion,
            emotion_scale=int(scale),
            response_policy=policy,
            empathy_mode=empathy_mode,
            user_emotion_label=getattr(svc, "last_user_emotion_label", None) if svc else None,
            affective_v2_enabled=True,
            trust=float(rel.trust) if rel else 0.5,
            warmth=float(rel.warmth) if rel else 0.4,
            relationship_stage=derive_stage(rel.trust, rel.warmth) if rel else "acquaintance",
            interpersonal_cue=(getattr(svc, "last_interpersonal_cue", None) or "") if svc else "",
            has_memories=bool((bullets or "").strip()),
            memory_bullets=bullets or "",
            locale="zh",
            user_v=user_v,
        )
        ctx.turn_type = infer_turn_type(ctx)
        ctx.reply_plan = self._reply_planner.build(ctx)
        return ctx
