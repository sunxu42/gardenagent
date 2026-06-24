"""Agent 回应策略合成：感知层 + 关系层 → ResponsePolicy → StrategyTags → ActuationPlan。"""

from __future__ import annotations

from dataclasses import dataclass

from agent.emotion.constants import EMOTION_SYNTHESIS_EMPATHY_GAIN, EMOTION_SYNTHESIS_WEIGHT_FLOOR
from agent.emotion.core.policy import ActuationPlan, ResponsePolicy, TurnAppraisalV2
from agent.emotion.core.relationship import RelationshipState, derive_stage
from agent.emotion.core.vad import ALL_EMOTIONS, VAD, project
from agent.emotion.synthesis.prosody_mapping import map_prosody
from agent.emotion.synthesis.strategy_tags import StrategyTags, derive_strategy_tags


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _is_hostile(appraisal: TurnAppraisalV2, relationship: RelationshipState) -> bool:
    cue = (appraisal.interpersonal_cue or "").strip()
    hostile_keywords = ("指责", "辱骂", "骂", "生气", "愤怒", "不满", "骗人", "胡说")
    if relationship.warmth < 0.3 and appraisal.user_v < -0.4:
        return True
    return any(k in cue for k in hostile_keywords)


@dataclass
class SynthesisResult:
    policy: ResponsePolicy
    actuation: ActuationPlan
    user_emotion_label: str
    tags: StrategyTags
    rule_id: str = "balanced_default"


def synthesize_response(
    appraisal: TurnAppraisalV2,
    relationship: RelationshipState,
    persona_baseline: VAD,
    *,
    empathy_gain: float = EMOTION_SYNTHESIS_EMPATHY_GAIN,
) -> SynthesisResult:
    user_vad = appraisal.user_vad()
    user_emotion_label, _ = project(user_vad, ALL_EMOTIONS)
    stage = derive_stage(relationship.trust, relationship.warmth)

    policy = ResponsePolicy()
    target = VAD(persona_baseline.v, persona_baseline.a, persona_baseline.d)
    rule_id = "balanced_default"

    if _is_hostile(appraisal, relationship):
        rule_id = "hostile_de_escalate"
        policy = ResponsePolicy(
            empathy_mode="de_escalate",
            stance="calm_professional",
            repair_action="apologize_if_mistake" if relationship.trust < 0.5 else "clarify_before_advise",
            directiveness=0.3,
        )
        target = VAD(0.0, min(0.35, persona_baseline.a), min(0.0, persona_baseline.d))
    elif user_vad.v > 0.5 and appraisal.user_weight >= 0.5:
        rule_id = "positive_celebrate"
        policy = ResponsePolicy(
            empathy_mode="celebrate_with",
            stance="warm_casual" if relationship.warmth >= 0.5 else "balanced",
            directiveness=0.55 if relationship.trust >= 0.6 else 0.4,
        )
        mirror = empathy_gain * max(0.45, relationship.warmth)
        if stage == "bonded":
            mirror = min(0.95, mirror + 0.1)
        target = VAD(
            _lerp(persona_baseline.v, user_vad.v, mirror),
            _lerp(persona_baseline.a, user_vad.a, mirror * 0.75),
            _lerp(persona_baseline.d, user_vad.d, mirror * 0.55),
        )
    elif user_vad.v < -0.3:
        if relationship.warmth >= 0.5:
            rule_id = "negative_warm_mirror"
            policy = ResponsePolicy(
                empathy_mode="mirror_warmth" if relationship.warmth >= 0.65 else "acknowledge_first",
                stance="warm_casual",
                directiveness=0.45,
            )
            mirror = empathy_gain * max(0.5, relationship.warmth)
            target = VAD(
                _lerp(persona_baseline.v, user_vad.v, mirror),
                _lerp(persona_baseline.a, min(user_vad.a, 0.5), mirror * 0.65),
                persona_baseline.d,
            )
        else:
            rule_id = "negative_guarded_ack"
            policy = ResponsePolicy(
                empathy_mode="acknowledge_first",
                stance="guarded_formal" if relationship.trust < 0.4 else "balanced",
                repair_action="clarify_before_advise" if relationship.trust < 0.4 else "none",
                directiveness=0.35,
            )
            target = VAD(
                _lerp(persona_baseline.v, user_vad.v, 0.35),
                min(persona_baseline.a, 0.4),
                persona_baseline.d,
            )
    else:
        rule_id = "neutral_baseline"
        policy = ResponsePolicy(
            stance="warm_casual" if relationship.warmth >= 0.6 else "balanced",
            directiveness=0.55 if relationship.trust >= 0.7 else 0.45,
        )
        target = persona_baseline

    if stage == "stranger" and rule_id != "hostile_de_escalate":
        rule_id = f"{rule_id}_stage_stranger"
        policy.stance = "guarded_formal"
        policy.repair_action = policy.repair_action if policy.repair_action != "none" else "clarify_before_advise"
        target = VAD(target.v, min(target.a, 0.45), target.d)
        policy.directiveness = min(policy.directiveness, 0.4)
    elif stage == "bonded" and rule_id not in ("hostile_de_escalate",):
        rule_id = f"{rule_id}_stage_bonded"
        policy.directiveness = max(policy.directiveness, 0.55)
        if policy.stance == "balanced":
            policy.stance = "warm_casual"
    elif relationship.trust < 0.4 and policy.empathy_mode != "de_escalate":
        policy.stance = "guarded_formal"
        policy.repair_action = policy.repair_action if policy.repair_action != "none" else "clarify_before_advise"
        target = VAD(target.v, min(target.a, 0.45), target.d)
        policy.directiveness = min(policy.directiveness, 0.4)
    elif relationship.trust >= 0.7:
        policy.directiveness = max(policy.directiveness, 0.55)

    target = VAD(
        _clamp(target.v, -1.0, 1.0),
        _clamp(target.a, 0.0, 1.0),
        _clamp(target.d, -1.0, 1.0),
    ).clamp()

    weight = max(appraisal.user_weight, appraisal.rel_weight * 0.8)
    weight = max(EMOTION_SYNTHESIS_WEIGHT_FLOOR, min(0.9, weight))

    tags = derive_strategy_tags(policy, user_emotion=user_emotion_label)
    prosody = map_prosody(tags.tts_profile, target)
    actuation = ActuationPlan(
        vad_target=target,
        weight=weight,
        speech_rate=prosody.speech_rate,
        pitch=prosody.pitch,
        loudness_rate=prosody.loudness_rate,
        tts_emotion=prosody.emotion,
        tts_emotion_scale=prosody.emotion_scale,
    )
    return SynthesisResult(
        policy=policy,
        actuation=actuation,
        user_emotion_label=user_emotion_label,
        tags=tags,
        rule_id=rule_id,
    )
