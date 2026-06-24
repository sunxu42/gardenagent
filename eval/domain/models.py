from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from eval.api.schemas import AgentAffectSnapshot

EvalTier = Literal["smoke", "judge", "exploratory"]
EvalMode = Literal["scenario", "exploratory"]
RunStatus = Literal["running", "completed", "failed", "cancelled"]


class AssertionStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARN = "warn"


@dataclass(frozen=True)
class ToolEvent:
    name: str
    detail: str = ""


@dataclass(frozen=True)
class TurnObservation:
    round: int
    user_text: str
    assistant_text: str
    tool_events: tuple[ToolEvent, ...] = ()
    agent_affect: AgentAffectSnapshot | None = None
    latency_ms: float | None = None
    raw_updates: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssertionResult:
    name: str
    status: AssertionStatus
    message: str
    expected: Any = None
    actual: Any = None


@dataclass(frozen=True)
class JudgeMetricResult:
    name: str
    score: float
    passed: bool
    threshold: float
    reason: str
    blocking: bool = False


@dataclass(frozen=True)
class EvalRunResult:
    run_id: str
    scenario_id: str
    tier: EvalTier
    mode: EvalMode
    status: RunStatus
    observations: tuple[TurnObservation, ...]
    assertions: tuple[AssertionResult, ...] = ()
    judge_results: tuple[JudgeMetricResult, ...] = ()
    judge_overall_passed: bool | None = None
    error: str | None = None

    @property
    def assertions_all_passed(self) -> bool:
        return all(
            item.status in {AssertionStatus.PASS, AssertionStatus.WARN, AssertionStatus.SKIP}
            for item in self.assertions
        )
