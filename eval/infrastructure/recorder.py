from __future__ import annotations

from datetime import UTC, datetime
from time import monotonic
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
from eval.domain.progress import EvalProgressEvent
from eval.infrastructure.record import EvalRunRecord, PersistedEvent, RunEnvironment, RunTelemetry

EVENT_CAP = 80


class RunRecorder:
    """Collects progress events and phase timings for one eval run."""

    def __init__(
        self,
        *,
        run_id: str,
        mode: EvalMode,
        tier: EvalTier,
        scenario_id: str,
        environment: RunEnvironment,
        started_at: datetime | None = None,
    ) -> None:
        self._run_id = run_id
        self._mode = mode
        self._tier = tier
        self._scenario_id = scenario_id
        self._environment = environment
        self._started_at = started_at or datetime.now(tz=UTC)
        self._events: list[PersistedEvent] = []
        self._telemetry = RunTelemetry()
        self._phase_started: dict[str, float] = {}
        self._phase_durations: dict[str, int] = {}

    def set_telemetry(self, **kwargs: Any) -> None:
        """Merge telemetry fields such as cold-start flags."""

        phase_durations = dict(self._phase_durations)
        phase_durations.update(kwargs.pop("phase_durations_ms", {}) or {})
        self._phase_durations = phase_durations
        self._telemetry = RunTelemetry(
            agent_cold_start=bool(kwargs.get("agent_cold_start", self._telemetry.agent_cold_start)),
            agent_reused=bool(kwargs.get("agent_reused", self._telemetry.agent_reused)),
            phase_durations_ms=dict(self._phase_durations),
            totals=dict(kwargs.get("totals") or self._telemetry.totals),
        )

    def mark_phase_start(self, phase: str) -> None:
        """Record the start of a named phase."""

        self._phase_started[phase] = monotonic()

    def mark_phase_end(self, phase: str) -> None:
        """Accumulate elapsed time for a named phase."""

        started = self._phase_started.pop(phase, None)
        if started is None:
            return
        elapsed_ms = int((monotonic() - started) * 1000)
        self._phase_durations[phase] = self._phase_durations.get(phase, 0) + elapsed_ms

    def record(self, event: EvalProgressEvent) -> None:
        """Append one progress event with an ISO timestamp."""

        at = datetime.now(tz=UTC).isoformat()
        self._events.append(
            PersistedEvent(type=event.type, at=at, payload=dict(event.payload))
        )
        if len(self._events) > EVENT_CAP:
            self._events = self._events[-EVENT_CAP:]

    def record_ws_payload(self, payload: dict[str, object]) -> None:
        """Record a WebSocket-shaped payload (e.g. setup progress)."""

        event_type = str(payload.get("type", "eval_progress"))
        nested = {key: value for key, value in payload.items() if key not in {"type", "run_id"}}
        self.record(
            EvalProgressEvent(
                type=event_type,  # type: ignore[arg-type]
                run_id=str(payload.get("run_id", self._run_id)),
                payload=nested,
            )
        )

    def build(
        self,
        *,
        status: RunStatus,
        observations: tuple[TurnObservation, ...] = (),
        assertions: tuple[AssertionResult, ...] = (),
        judge_results: tuple[JudgeMetricResult, ...] = (),
        judge_overall_passed: bool | None = None,
        error: str | None = None,
        exploratory_config: EmotionEvalRequest | None = None,
        scores: tuple[EmotionMetricScore, ...] = (),
        summary: EvalSummary | None = None,
    ) -> EvalRunRecord:
        """Build the final record with timing metadata."""

        finished_at = datetime.now(tz=UTC)
        duration_ms = int((finished_at - self._started_at).total_seconds() * 1000)
        telemetry = RunTelemetry(
            agent_cold_start=self._telemetry.agent_cold_start,
            agent_reused=self._telemetry.agent_reused,
            phase_durations_ms=dict(self._phase_durations),
            totals=dict(self._telemetry.totals),
        )
        return EvalRunRecord(
            run_id=self._run_id,
            mode=self._mode,
            tier=self._tier,
            status=status,
            scenario_id=self._scenario_id,
            started_at=self._started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_ms=duration_ms,
            environment=self._environment,
            telemetry=telemetry,
            observations=observations,
            assertions=assertions,
            judge_results=judge_results,
            judge_overall_passed=judge_overall_passed,
            scores=scores,
            summary=summary,
            exploratory_config=exploratory_config,
            events=tuple(self._events),
            error=error,
        )
