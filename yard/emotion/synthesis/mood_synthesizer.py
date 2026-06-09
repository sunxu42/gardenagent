"""Agent 回应策略合成：感知层 + 关系层 → ResponsePolicy → ActuationPlan。"""

from __future__ import annotations

from dataclasses import dataclass

from yard.emotion.core.policy import ActuationPlan, ResponsePolicy, TurnAppraisalV2
from yard.emotion.core.relationship import RelationshipState, derive_stage
from yard.emotion.core.vad import ALL_EMOTIONS, VAD, project


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _vad_to_prosody(vad: VAD) -> tuple[int, int]:
    speech_rate = int(max(-50, min(50, round((vad.a - 0.35) * 40))))
    pitch = int(max(-12, min(12, round(vad.v * 8 + (vad.a - 0.3) * 6))))
    return speech_rate, pitch


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
    rule_id: str = "balanced_default"


def synthesize_response(
    appraisal: TurnAppraisalV2,
    relationship: RelationshipState,
    persona_baseline: VAD,
    *,
    empathy_gain: float = 0.6,
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
        mirror = empathy_gain * max(0.3, relationship.warmth)
        if stage == "bonded":
            mirror = min(0.95, mirror + 0.1)
        target = VAD(
            _lerp(persona_baseline.v, user_vad.v, mirror),
            _lerp(persona_baseline.a, user_vad.a, mirror * 0.7),
            _lerp(persona_baseline.d, user_vad.d, mirror * 0.5),
        )
    elif user_vad.v < -0.3:
        if relationship.warmth >= 0.5:
            rule_id = "negative_warm_mirror"
            policy = ResponsePolicy(
                empathy_mode="mirror_warmth" if relationship.warmth >= 0.65 else "acknowledge_first",
                stance="warm_casual",
                directiveness=0.45,
            )
            mirror = empathy_gain * relationship.warmth
            target = VAD(
                _lerp(persona_baseline.v, user_vad.v, mirror),
                _lerp(persona_baseline.a, min(user_vad.a, 0.5), mirror * 0.6),
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
                _lerp(persona_baseline.v, user_vad.v, 0.25),
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
    weight = max(0.2, min(0.9, weight))

    speech_rate, pitch = _vad_to_prosody(target)
    actuation = ActuationPlan(
        vad_target=target,
        weight=weight,
        speech_rate=speech_rate,
        pitch=pitch,
    )
    return SynthesisResult(
        policy=policy,
        actuation=actuation,
        user_emotion_label=user_emotion_label,
        rule_id=rule_id,
    )
