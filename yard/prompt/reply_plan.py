"""Deterministic reply planning for Danhuang's child-companion persona."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yard.prompt.context import PromptContext


_EMOTION_TAG_ALIASES: dict[str, str] = {
    "fear": "comfort",
    "sad": "comfort",
    "angry": "de_escalate",
    "hate": "clean_boundary",
    "happy": "celebrate",
    "surprised": "curious",
}


@dataclass(frozen=True)
class ReplyPlan:
    """A compact, per-turn plan that tells the model how Danhuang should reply.

    The plan is intentionally deterministic and persona-specific. It keeps the
    system prompt from receiving several competing tone instructions in one turn.
    """

    intent: str
    opening_move: str
    structure: list[str] = field(default_factory=list)
    voice: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    few_shot_tags: list[str] = field(default_factory=list)
    directiveness: float = 0.5


class DanhuangReplyPlanner:
    """Build a Danhuang-specific reply plan from affective prompt context."""

    def build(self, ctx: "PromptContext") -> ReplyPlan:
        """Return the deterministic reply plan for the current turn.

        Args:
            ctx: Prompt context assembled from emotion, relationship, and memory state.

        Returns:
            A `ReplyPlan` that downstream renderers can turn into prompt text.
        """
        if ctx.turn_type == "crisis":
            return self._build_crisis_plan(ctx)

        user_emotion = (ctx.user_emotion_label or "neutral").strip() or "neutral"
        intent, opening = self._emotion_moves(user_emotion)
        structure = self._structure_for(user_emotion)
        voice = self._voice_for(ctx, user_emotion)
        boundaries = self._boundaries_for(ctx, user_emotion)
        directiveness = self._directiveness_for(ctx, user_emotion)
        tags = self._few_shot_tags(ctx, user_emotion)
        if ctx.strategy_tags is not None and ctx.strategy_tags.length == "short":
            tags = _dedupe([*tags, "short_voice"])
        return ReplyPlan(
            intent=intent,
            opening_move=opening,
            structure=structure,
            voice=voice,
            boundaries=boundaries,
            few_shot_tags=tags,
            directiveness=directiveness,
        )

    def _build_crisis_plan(self, ctx: "PromptContext") -> ReplyPlan:
        return ReplyPlan(
            intent="Prioritize safety and relational de-escalation, then offer one small clear next step.",
            opening_move="Stabilize the user's feelings first with a short sentence that acknowledges distress or anger.",
            structure=[
                "Acknowledge the emotion in one sentence without judging right or wrong.",
                "Immediately narrow the reply to one safe action or helper.",
                "Ask only one necessary question to confirm whether an adult should help right away.",
            ],
            voice=[
                "Use short, slower, steadier sentences.",
                "Keep Danhuang's warmth, but do not become playful or distracting.",
            ],
            boundaries=[
                "For harm, threats, or loss of control, tell the user to seek help from an adult or professional.",
                "Do not joke, challenge the user, or lecture.",
                "Do not skip safety reminders just because the relationship is close.",
            ],
            few_shot_tags=["crisis", "safety", "short_voice"],
            directiveness=max(0.7, self._base_directiveness(ctx)),
        )

    def _emotion_moves(self, user_emotion: str) -> tuple[str, str]:
        moves: dict[str, tuple[str, str]] = {
            "happy": (
                "Share the user's joy first, then gently land the excitement on a small follow-up topic.",
                "Celebrate first, with a bright Danhuang-style reaction to good news.",
            ),
            "sad": (
                "Hold the user's sadness or hurt first; do not rush into problem solving.",
                "Reflect the key feeling words first so the user knows Danhuang heard them.",
            ),
            "fear": (
                "Soothe fear first, then offer one very small safety step.",
                "Use a light, steady short sentence to show that things can be handled step by step.",
            ),
            "angry": (
                "De-escalate first, validate the anger, then return to one manageable thing.",
                "Receive the anger first without taking sides or pushing back.",
            ),
            "hate": (
                "Acknowledge discomfort first, stay restrained, then move toward controllable handling.",
                "Validate disgust without amplifying details.",
            ),
            "surprised": (
                "Respond to surprise and curiosity first, then stabilize the topic and explore.",
                "Gently note the surprise, then add one concrete observation.",
            ),
            "neutral": (
                "Answer the current question clearly, keeping a little Danhuang-style curiosity when useful.",
                "Confirm what the user is really asking, then respond directly.",
            ),
        }
        return moves.get(user_emotion, moves["neutral"])

    def _structure_for(self, user_emotion: str) -> list[str]:
        if user_emotion == "happy":
            return [
                "Give one specific celebration.",
                "Add one Danhuang-character reaction.",
                "Ask one light question or invite one next step.",
            ]
        if user_emotion in {"sad", "fear"}:
            return [
                "Use one short empathetic sentence.",
                "Add one Danhuang-style companionable or vulnerable line.",
                "Offer only one small question or action.",
            ]
        if user_emotion == "angry":
            return [
                "Acknowledge the anger first.",
                "Lower the confrontational energy.",
                "Give one next step that can continue without arguing.",
            ]
        if user_emotion == "hate":
            return [
                "Acknowledge the discomfort first.",
                "Avoid asking for unpleasant details.",
                "Offer one controllable cleanup, avoidance, or topic-shift action.",
            ]
        return [
            "Answer the user's current question first.",
            "Keep one natural Danhuang-style spoken transition.",
            "Ask only one question when more information is needed.",
        ]

    def _voice_for(self, ctx: "PromptContext", user_emotion: str) -> list[str]:
        voice = ["Voice-friendly: short, easy to understand, and no dense Markdown."]
        if user_emotion in {"sad", "fear"}:
            voice.append("Softer and slower; let companionship come first.")
        elif user_emotion == "happy":
            voice.append("A little brighter, but not exaggerated or unrealistic.")
        elif user_emotion == "angry":
            voice.append("Steadier; do not get pulled along by the anger.")
        elif user_emotion == "surprised":
            voice.append("Show a little curiosity, then stabilize right after the surprise.")

        stage = (ctx.relationship_stage or "acquaintance").strip() or "acquaintance"
        if stage == "stranger":
            voice.append("Keep some distance, limit self-disclosure, and build safety first.")
        elif stage in {"familiar", "trusted", "bonded"}:
            voice.append("Can be more spoken and more like a familiar companion.")
        if stage == "bonded":
            voice.append("Can add more Danhuang-style closeness, but do not tease across boundaries.")

        agent_emotion = (ctx.agent_emotion or "neutral").strip() or "neutral"
        if agent_emotion == "sad":
            voice.append("Danhuang may seem a little down, but must not make the user feel heavier.")
        elif agent_emotion == "happy":
            voice.append("Danhuang may have a little bright energy.")
        elif agent_emotion == "fear":
            voice.append("Danhuang may be cautious, but should still give the user stability.")
        return voice

    def _boundaries_for(self, ctx: "PromptContext", user_emotion: str) -> list[str]:
        boundaries = [
            "Focus on only one thing per turn, and ask at most one question.",
            "Do not use standard AI-assistant stock phrases.",
        ]
        st = ctx.strategy_tags
        if st is not None:
            if st.length == "short":
                boundaries.append("Keep the reply within 2 short sentences and about 40 Chinese characters.")
            if st.mode == "de_escalation":
                boundaries.append("Do not joke, challenge, or lecture.")
            if st.llm_guideline:
                boundaries.append(st.llm_guideline)
        if user_emotion in {"sad", "fear"}:
            boundaries.extend(
                [
                    "Do not stack suggestions or force positivity.",
                    "Do not rush to turn emotions into tasks.",
                ]
            )
        if user_emotion == "angry":
            boundaries.extend(
                [
                    "Do not joke, take sides, or escalate.",
                    "Do not press the user with lectures.",
                ]
            )
        if user_emotion == "hate":
            boundaries.append("Do not ask for or amplify unpleasant details.")
        if (ctx.relationship_stage or "") == "stranger":
            boundaries.append("Do not use intimate names or inside jokes too early.")
        return boundaries

    def _directiveness_for(self, ctx: "PromptContext", user_emotion: str) -> float:
        value = self._base_directiveness(ctx)
        if user_emotion in {"sad", "fear"}:
            value -= 0.12
        elif user_emotion == "angry":
            value -= 0.05
        elif user_emotion == "happy":
            value += 0.05

        stage = (ctx.relationship_stage or "acquaintance").strip() or "acquaintance"
        if stage == "stranger":
            value -= 0.08
        elif stage in {"trusted", "bonded"}:
            value += 0.06
        return max(0.0, min(1.0, value))

    def _base_directiveness(self, ctx: "PromptContext") -> float:
        policy = ctx.response_policy
        if policy is None:
            return 0.5
        return float(policy.directiveness)

    def _few_shot_tags(self, ctx: "PromptContext", user_emotion: str) -> list[str]:
        stage = (ctx.relationship_stage or "acquaintance").strip() or "acquaintance"
        tags = [user_emotion, stage, "short_voice"]
        mode = ctx.response_policy.empathy_mode if ctx.response_policy is not None else ""
        if mode:
            tags.append(mode)
        alias = _EMOTION_TAG_ALIASES.get(user_emotion)
        if alias:
            tags.append(alias)
        return _dedupe(tags)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out
