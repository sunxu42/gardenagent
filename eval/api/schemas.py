from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EvalStatus = Literal["running", "completed", "failed", "cancelled"]
EvalVerdict = Literal["pass", "warning", "fail"]
EvalTier = Literal["smoke", "judge", "exploratory"]
EvalMode = Literal["scenario", "exploratory"]
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
    latency_ms: float | None = None
    raw_updates: list[str] = Field(default_factory=list)


class RunEnvironmentDTO(BaseModel):
    """Environment fingerprint for one eval run."""

    git_commit: str | None = None
    git_dirty: bool | None = None
    agent_model: str | None = None
    eval_judge_model: str | None = None
    prompt_manifest_hash: str | None = None
    python_version: str | None = None


class RunTelemetryDTO(BaseModel):
    """Runtime telemetry for one eval run."""

    agent_cold_start: bool | None = None
    agent_reused: bool | None = None
    phase_durations_ms: dict[str, int] = Field(default_factory=dict)
    totals: dict[str, int] = Field(default_factory=dict)


class PersistedEventDTO(BaseModel):
    """One persisted progress event."""

    type: str
    at: str
    payload: dict[str, object] = Field(default_factory=dict)


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


class AssertionResultDTO(BaseModel):
    """One L0 assertion result for API consumers."""

    name: str
    status: Literal["pass", "fail", "skip", "warn"]
    message: str


class JudgeMetricScoreDTO(BaseModel):
    """One DeepEval judge metric result."""

    name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    threshold: float = Field(ge=0.0, le=1.0)
    reason: str


class ScenarioSummary(BaseModel):
    """Summary metadata for one scenario fixture."""

    id: str
    description: str
    domain: str
    tier: EvalTier


class EvalRunRequest(BaseModel):
    """Unified evaluation request."""

    mode: EvalMode
    scenario_id: str | None = None
    exploratory: EmotionEvalRequest | None = None
    persist: bool = True


class EvalRunResponse(BaseModel):
    """Unified evaluation response."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    mode: EvalMode
    tier: EvalTier
    status: EvalStatus
    scenario_id: str | None = None
    observations: list[EmotionTurnResult] = Field(default_factory=list)
    assertions: list[AssertionResultDTO] = Field(default_factory=list)
    judge: list[JudgeMetricScoreDTO] = Field(default_factory=list)
    judge_overall_passed: bool | None = None
    scores: list[EmotionMetricScore] = Field(default_factory=list)
    summary: EvalSummary | None = None
    error: EvalError | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    environment: RunEnvironmentDTO | None = None
    telemetry: RunTelemetryDTO | None = None
    events: list[PersistedEventDTO] = Field(default_factory=list)
    exploratory_config: EmotionEvalRequest | None = None


class ScenarioEvalRequest(BaseModel):
    """Run one scripted scenario by id."""

    model_config = ConfigDict(populate_by_name=True)

    scenario_id: str
    client_id: str | None = None
    async_run: bool = Field(default=False, alias="async")
    persist: bool = True


class EvalRunStartedResponse(BaseModel):
    """Immediate response when an async scenario eval is accepted."""

    run_id: str
    scenario_id: str
    tier: EvalTier
    status: Literal["running"] = "running"


class EvalRunSummary(BaseModel):
    """Summary row for eval run history."""

    run_id: str
    scenario_id: str
    tier: EvalTier
    mode: EvalMode = "scenario"
    status: EvalStatus
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    assertions_passed: bool | None = None
    judge_overall_passed: bool | None = None


class EvalRunCancelResponse(BaseModel):
    """Response after cancelling an eval run."""

    run_id: str
    status: Literal["cancelled"] = "cancelled"


class EmotionSupportRunRequest(EmotionEvalRequest):
    """Run exploratory emotion evaluation, optionally async with WS progress."""

    model_config = ConfigDict(populate_by_name=True)

    client_id: str | None = None
    async_run: bool = Field(default=False, alias="async")


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
