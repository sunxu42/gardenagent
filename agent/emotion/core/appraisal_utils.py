"""Appraisal 后处理：关系增量校验。"""

from __future__ import annotations

from agent.emotion.core.policy import TurnAppraisalV2


def sanitize_relationship_deltas(appraisal: TurnAppraisalV2) -> TurnAppraisalV2:
    """弱化与用户情绪明显矛盾的 trust/warmth 增量。"""
    trust_d = float(appraisal.trust_delta)
    warmth_d = float(appraisal.warmth_delta)
    uv = float(appraisal.user_v)

    if uv < -0.35:
        if trust_d > 0.04:
            trust_d = 0.04
        if warmth_d > 0.03:
            warmth_d = 0.03
    elif uv > 0.45 and appraisal.user_weight >= 0.45:
        if trust_d < -0.04:
            trust_d = -0.04

    cue = (appraisal.interpersonal_cue or "").strip()
    hostile = any(k in cue for k in ("骂", "指责", "侮辱", "威胁", "骗人"))
    if hostile:
        if trust_d > 0:
            trust_d = min(trust_d, 0.0)
        if warmth_d > 0:
            warmth_d = min(warmth_d, 0.0)

    return appraisal.model_copy(
        update={
            "trust_delta": max(-0.15, min(0.15, trust_d)),
            "warmth_delta": max(-0.15, min(0.15, warmth_d)),
        }
    )
