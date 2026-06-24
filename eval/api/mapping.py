from __future__ import annotations

from eval.api.schemas import (
    AssertionResultDTO,
    EmotionEvalResponse,
    EmotionMetricScore,
    EmotionTurnResult,
    EvalRunResponse,
    EvalSummary,
    JudgeMetricScoreDTO,
    PersistedEventDTO,
    RunEnvironmentDTO,
    RunTelemetryDTO,
)
from eval.domain.emotion_metrics import summarize_scores
from eval.domain.models import EvalRunResult, TurnObservation
from eval.infrastructure.record import EvalRunRecord


def observation_to_turn(observation: TurnObservation) -> EmotionTurnResult:
    """Map an internal observation to the public turn DTO."""

    return EmotionTurnResult(
        round=observation.round,
        user=observation.user_text,
        assistant=observation.assistant_text,
        agent_affect=observation.agent_affect,
        latency_ms=observation.latency_ms,
        raw_updates=list(observation.raw_updates),
    )


def to_eval_run_response_from_record(record: EvalRunRecord) -> EvalRunResponse:
    """Map a persisted record to the unified API response."""

    observations = [observation_to_turn(item) for item in record.observations]
    assertions = [
        AssertionResultDTO(
            name=item.name,
            status=item.status.value,
            message=item.message,
        )
        for item in record.assertions
    ]
    judge = [
        JudgeMetricScoreDTO(
            name=item.name,
            score=item.score,
            passed=item.passed,
            threshold=item.threshold,
            reason=item.reason,
        )
        for item in record.judge_results
    ]
    scores = list(record.scores)
    summary: EvalSummary | None = record.summary
    if record.mode == "exploratory" and summary is None and scores:
        summary = summarize_scores(scores)

    return EvalRunResponse(
        run_id=record.run_id,
        mode=record.mode,
        tier=record.tier,
        status=record.status,
        scenario_id=record.scenario_id,
        observations=observations,
        assertions=assertions,
        judge=judge,
        judge_overall_passed=record.judge_overall_passed,
        scores=scores,
        summary=summary,
        error=None if record.error is None else _error_from_message(record.error),
        started_at=record.started_at,
        finished_at=record.finished_at,
        duration_ms=record.duration_ms,
        environment=RunEnvironmentDTO(
            git_commit=record.environment.git_commit,
            git_dirty=record.environment.git_dirty,
            agent_model=record.environment.agent_model,
            eval_judge_model=record.environment.eval_judge_model,
            prompt_manifest_hash=record.environment.prompt_manifest_hash,
            python_version=record.environment.python_version,
        ),
        telemetry=RunTelemetryDTO(
            agent_cold_start=record.telemetry.agent_cold_start,
            agent_reused=record.telemetry.agent_reused,
            phase_durations_ms=record.telemetry.phase_durations_ms,
            totals=record.telemetry.totals,
        ),
        events=[
            PersistedEventDTO(type=item.type, at=item.at, payload=item.payload)
            for item in record.events
        ],
        exploratory_config=record.exploratory_config,
    )


def to_eval_run_response(result: EvalRunResult) -> EvalRunResponse:
    """Map an internal run result to the unified API response."""

    record = EvalRunRecord(
        run_id=result.run_id,
        mode=result.mode,
        tier=result.tier,
        status=result.status,
        scenario_id=result.scenario_id,
        observations=result.observations,
        assertions=result.assertions,
        judge_results=result.judge_results,
        judge_overall_passed=result.judge_overall_passed,
        error=result.error,
        schema_version=0,
    )
    return to_eval_run_response_from_record(record)


def to_emotion_eval_response(
    result: EvalRunResult,
    *,
    scenario_request,
) -> EmotionEvalResponse:
    """Map an exploratory run result to the legacy emotion eval response."""

    observations = [observation_to_turn(item) for item in result.observations]
    scores = [
        EmotionMetricScore(
            name=item.name,
            score=item.score,
            reason=item.reason,
            evidence=[item.reason],
        )
        for item in result.judge_results
    ]
    return EmotionEvalResponse(
        session_id=result.run_id,
        status=result.status,
        scenario=scenario_request,
        turns=observations,
        scores=scores,
        summary=summarize_scores(scores) if scores else None,
        error=_error_from_message(result.error) if result.error else None,
    )


def _error_from_message(message: str):
    from eval.api.schemas import EvalError

    return EvalError(code="eval_run_failed", message=message)
