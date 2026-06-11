from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EvalStatus = Literal["completed", "failed"]
EvalVerdict = Literal["pass", "warning", "fail"]
InitialMood = Literal["anxious", "sad", "angry", "lonely", "stressed", "neutral"]


class EmotionEvalRequest(BaseModel):
    """Scenario selected by the user for one isolated evaluation run."""

    background: str = Field(min_length=1, max_length=2000)
    initial_mood: InitialMood
    rounds: int = Field(default=5, ge=1, le=8)
    goal: str = Field(default="评估 agent 的情绪支持质量", min_length=1, max_length=1000)


class AgentAffectSnapshot(BaseModel):
    """Best-effort affect state captured after one assistant turn."""

    emotion: str | None = None
    vad: dict[str, float] | None = None
    relationship_stage: str | None = None


class EmotionTurnResult(BaseModel):
    """One simulated user turn and the assistant response under test."""

    round: int = Field(ge=1)
    user: str
    assistant: str
    agent_affect: AgentAffectSnapshot | None = None


class EmotionMetricScore(BaseModel):
    """DeepEval score plus evaluator explanation."""

    name: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[str] = Field(default_factory=list)


class EvalSummary(BaseModel):
    """Aggregated conclusion for frontend display."""

    overall_score: float = Field(ge=0.0, le=1.0)
    verdict: EvalVerdict
    conclusion: str
    improvement_suggestions: list[str] = Field(default_factory=list)


class EvalError(BaseModel):
    """Machine-readable error returned by the eval API."""

    code: str
    message: str


class EmotionEvalResponse(BaseModel):
    """HTTP response for a completed or failed emotion evaluation."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    status: EvalStatus
    scenario: EmotionEvalRequest | None = None
    turns: list[EmotionTurnResult] = Field(default_factory=list)
    scores: list[EmotionMetricScore] = Field(default_factory=list)
    summary: EvalSummary | None = None
    error: EvalError | None = None
