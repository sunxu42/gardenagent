from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from eval.api.schemas import EmotionEvalRequest, EmotionMetricScore, EvalSummary
from eval.domain.models import (
    AssertionResult,
    EvalMode,
    EvalTier,
    JudgeMetricResult,
    RunStatus,
    TurnObservation,
)


@dataclass(frozen=True)
class RunEnvironment:
    """Captured environment fingerprint for one eval run."""

    git_commit: str | None = None
    git_dirty: bool | None = None
    agent_model: str | None = None
    eval_judge_model: str | None = None
    prompt_manifest_hash: str | None = None
    python_version: str = ""


@dataclass(frozen=True)
class RunTelemetry:
    """Runtime telemetry collected during one eval run."""

    agent_cold_start: bool = False
    agent_reused: bool = True
    phase_durations_ms: dict[str, int] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class PersistedEvent:
    """One progress event persisted with a timestamp."""

    type: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalRunRecord:
    """Full persisted evaluation run (schema v1)."""

    run_id: str
    mode: EvalMode
    tier: EvalTier
    status: RunStatus
    scenario_id: str
    schema_version: int = 1
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    environment: RunEnvironment = field(default_factory=RunEnvironment)
    telemetry: RunTelemetry = field(default_factory=RunTelemetry)
    observations: tuple[TurnObservation, ...] = ()
    assertions: tuple[AssertionResult, ...] = ()
    judge_results: tuple[JudgeMetricResult, ...] = ()
    judge_overall_passed: bool | None = None
    scores: tuple[EmotionMetricScore, ...] = ()
    summary: EvalSummary | None = None
    exploratory_config: EmotionEvalRequest | None = None
    events: tuple[PersistedEvent, ...] = ()
    error: str | None = None
