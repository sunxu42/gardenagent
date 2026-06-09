"""关系状态：trust / warmth 持久化、阶段派生、增量更新与时间衰减。"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Literal

RelationshipStage = Literal["stranger", "acquaintance", "familiar", "trusted", "bonded"]


@dataclass
class RelationshipState:
    trust: float = 0.5
    warmth: float = 0.4
    baseline_trust: float = 0.5
    baseline_warmth: float = 0.4
    updated_at: float = 0.0

    def clamp(self) -> RelationshipState:
        return RelationshipState(
            trust=max(0.0, min(1.0, self.trust)),
            warmth=max(0.0, min(1.0, self.warmth)),
            baseline_trust=max(0.0, min(1.0, self.baseline_trust)),
            baseline_warmth=max(0.0, min(1.0, self.baseline_warmth)),
            updated_at=self.updated_at,
        )

    def as_dict(self) -> dict:
        c = self.clamp()
        return {
            "trust": c.trust,
            "warmth": c.warmth,
            "baseline_trust": c.baseline_trust,
            "baseline_warmth": c.baseline_warmth,
            "updated_at": c.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> RelationshipState:
        return RelationshipState(
            trust=float(data.get("trust", 0.5)),
            warmth=float(data.get("warmth", 0.4)),
            baseline_trust=float(data.get("baseline_trust", 0.5)),
            baseline_warmth=float(data.get("baseline_warmth", 0.4)),
            updated_at=float(data.get("updated_at") or time.time()),
        ).clamp()


def derive_stage(trust: float, warmth: float) -> RelationshipStage:
    if trust >= 0.7 and warmth >= 0.7:
        return "bonded"
    if trust >= 0.7:
        return "trusted"
    if warmth >= 0.6:
        return "familiar"
    if trust < 0.3 and warmth < 0.3:
        return "stranger"
    return "acquaintance"


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def apply_relationship_delta(
    state: RelationshipState,
    *,
    trust_delta: float,
    warmth_delta: float,
    weight: float,
    alpha: float,
) -> RelationshipState:
    t = max(0.0, min(1.0, alpha * weight))
    trust = _lerp(state.trust, state.trust + trust_delta, t)
    warmth = _lerp(state.warmth, state.warmth + warmth_delta, t)
    return RelationshipState(
        trust=trust,
        warmth=warmth,
        baseline_trust=state.baseline_trust,
        baseline_warmth=state.baseline_warmth,
        updated_at=time.time(),
    ).clamp()


def decay_relationship(state: RelationshipState, *, dt_sec: float, tau_sec: float) -> RelationshipState:
    if dt_sec <= 0 or tau_sec <= 0:
        return state.clamp()
    beta = 1.0 - math.exp(-dt_sec / tau_sec)
    return RelationshipState(
        trust=_lerp(state.trust, state.baseline_trust, beta),
        warmth=_lerp(state.warmth, state.baseline_warmth, beta),
        baseline_trust=state.baseline_trust,
        baseline_warmth=state.baseline_warmth,
        updated_at=state.updated_at + dt_sec,
    ).clamp()
