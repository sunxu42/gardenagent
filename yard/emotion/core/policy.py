"""策略层与执行层模型：ResponsePolicy、ActuationPlan、TurnAppraisalV2。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from yard.emotion.core.vad import VAD

EmpathyMode = Literal[
    "neutral", "acknowledge_first", "mirror_warmth", "de_escalate", "celebrate_with"
]
Stance = Literal["balanced", "calm_professional", "warm_casual", "guarded_formal"]
RepairAction = Literal["none", "apologize_if_mistake", "clarify_before_advise"]


class ResponsePolicy(BaseModel):
    empathy_mode: EmpathyMode = "neutral"
    stance: Stance = "balanced"
    repair_action: RepairAction = "none"
    directiveness: float = Field(default=0.5, ge=0.0, le=1.0)


class ActuationPlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    vad_target: VAD
    weight: float = Field(ge=0.0, le=1.0)
    speech_rate: int = 0
    pitch: int = 0

    @classmethod
    def from_vad(cls, vad: VAD, *, weight: float) -> ActuationPlan:
        return cls(vad_target=vad.clamp(), weight=max(0.0, min(1.0, weight)))


class TurnAppraisalV2(BaseModel):
    user_v: float = Field(ge=-1.0, le=1.0)
    user_a: float = Field(ge=0.0, le=1.0)
    user_d: float = Field(ge=-1.0, le=1.0)
    user_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    trust_delta: float = Field(default=0.0, ge=-0.15, le=0.15)
    warmth_delta: float = Field(default=0.0, ge=-0.15, le=0.15)
    rel_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    interpersonal_cue: str = ""

    @field_validator("user_v", "user_d", mode="before")
    @classmethod
    def _clamp_vd(cls, v):
        return max(-1.0, min(1.0, float(v)))

    @field_validator("user_a", "user_weight", "rel_weight", mode="before")
    @classmethod
    def _clamp_01(cls, v):
        return max(0.0, min(1.0, float(v)))

    @field_validator("trust_delta", "warmth_delta", mode="before")
    @classmethod
    def _clamp_delta(cls, v):
        return max(-0.15, min(0.15, float(v)))

    def user_vad(self) -> VAD:
        return VAD(self.user_v, self.user_a, self.user_d).clamp()
