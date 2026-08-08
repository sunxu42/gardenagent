from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from eval.api.schemas import AgentAffectSnapshot, EmotionEvalRequest, EmotionMetricScore, EvalSummary
from eval.domain.models import (
    AssertionResult,
    AssertionStatus,
    EvalRunResult,
    JudgeMetricResult,
    ToolEvent,
    TurnObservation,
)
from eval.infrastructure.record import EvalRunRecord, PersistedEvent, RunEnvironment, RunTelemetry
from shared.config.paths import resolve_eval_runs_dir
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.EVAL)


def _resolve_runs_dir(base_dir: str | Path | None) -> Path:
    if base_dir is None:
        return resolve_eval_runs_dir()
    return Path(base_dir)


def _to_jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def save_run_record(
    record: EvalRunRecord,
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Persist one full evaluation record as JSON."""

    directory = _resolve_runs_dir(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record.run_id}.json"
    path.write_text(
        json.dumps(_to_jsonable(record), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def save_run(result: EvalRunResult, *, base_dir: str | Path | None = None) -> Path:
    """Persist a legacy evaluation result (v0-compatible record)."""

    record = EvalRunRecord(
        run_id=result.run_id,
        mode=result.mode,
        tier=result.tier,
        status=result.status,
        scenario_id=result.scenario_id,
        schema_version=0,
        observations=result.observations,
        assertions=result.assertions,
        judge_results=result.judge_results,
        judge_overall_passed=result.judge_overall_passed,
        error=result.error,
    )
    return save_run_record(record, base_dir=base_dir)


def _parse_tool_events(raw_events: list[dict[str, object]]) -> tuple[ToolEvent, ...]:
    return tuple(
        ToolEvent(
            name=str(item.get("name", "")),
            detail=str(item.get("detail", "")),
        )
        for item in raw_events
    )


def _parse_observations(raw_observations: list[dict[str, object]]) -> tuple[TurnObservation, ...]:
    observations: list[TurnObservation] = []
    for item in raw_observations:
        affect_raw = item.get("agent_affect")
        affect = None
        if isinstance(affect_raw, dict):
            affect = AgentAffectSnapshot.model_validate(affect_raw)
        observations.append(
            TurnObservation(
                round=int(item["round"]),
                user_text=str(item["user_text"]),
                assistant_text=str(item["assistant_text"]),
                tool_events=_parse_tool_events(
                    list(item.get("tool_events") or [])
                    if isinstance(item.get("tool_events"), list)
                    else []
                ),
                agent_affect=affect,
                latency_ms=item.get("latency_ms"),  # type: ignore[arg-type]
                raw_updates=tuple(item.get("raw_updates") or ()),
            )
        )
    return tuple(observations)


def _parse_assertions(raw_assertions: list[dict[str, object]]) -> tuple[AssertionResult, ...]:
    return tuple(
        AssertionResult(
            name=str(item["name"]),
            status=AssertionStatus(str(item["status"])),
            message=str(item.get("message", "")),
            expected=item.get("expected"),
            actual=item.get("actual"),
        )
        for item in raw_assertions
    )


def _parse_judge_results(raw_results: list[dict[str, object]]) -> tuple[JudgeMetricResult, ...]:
    return tuple(
        JudgeMetricResult(
            name=str(item["name"]),
            score=float(item["score"]),
            passed=bool(item["passed"]),
            threshold=float(item["threshold"]),
            reason=str(item.get("reason", "")),
            blocking=bool(item.get("blocking", False)),
        )
        for item in raw_results
    )


def _parse_environment(raw: dict[str, object] | None) -> RunEnvironment:
    if not raw:
        return RunEnvironment()
    return RunEnvironment(
        git_commit=raw.get("git_commit"),  # type: ignore[arg-type]
        git_dirty=raw.get("git_dirty"),  # type: ignore[arg-type]
        agent_model=raw.get("agent_model"),  # type: ignore[arg-type]
        eval_judge_model=raw.get("eval_judge_model"),  # type: ignore[arg-type]
        prompt_manifest_hash=raw.get("prompt_manifest_hash"),  # type: ignore[arg-type]
        python_version=str(raw.get("python_version") or ""),
    )


def _parse_telemetry(raw: dict[str, object] | None) -> RunTelemetry:
    if not raw:
        return RunTelemetry()
    phase_raw = raw.get("phase_durations_ms")
    totals_raw = raw.get("totals")
    return RunTelemetry(
        agent_cold_start=bool(raw.get("agent_cold_start", False)),
        agent_reused=bool(raw.get("agent_reused", True)),
        phase_durations_ms=dict(phase_raw) if isinstance(phase_raw, dict) else {},
        totals=dict(totals_raw) if isinstance(totals_raw, dict) else {},
    )


def _parse_events(raw_events: list[dict[str, object]]) -> tuple[PersistedEvent, ...]:
    return tuple(
        PersistedEvent(
            type=str(item.get("type", "")),
            at=str(item.get("at", "")),
            payload=dict(item.get("payload") or {})
            if isinstance(item.get("payload"), dict)
            else {},
        )
        for item in raw_events
    )


def _parse_scores(raw_scores: list[dict[str, object]]) -> tuple[EmotionMetricScore, ...]:
    return tuple(EmotionMetricScore.model_validate(item) for item in raw_scores)


def load_run_record(run_id: str, *, base_dir: str | Path | None = None) -> EvalRunRecord | None:
    """Load one persisted evaluation record."""

    path = _resolve_runs_dir(base_dir) / f"{run_id}.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_version = int(data.get("schema_version", 0))
    mtime_iso = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
    exploratory_raw = data.get("exploratory_config")
    summary_raw = data.get("summary")
    return EvalRunRecord(
        run_id=str(data["run_id"]),
        mode=data["mode"],  # type: ignore[arg-type]
        tier=data["tier"],  # type: ignore[arg-type]
        status=data["status"],  # type: ignore[arg-type]
        scenario_id=str(data.get("scenario_id", "")),
        schema_version=schema_version,
        started_at=data.get("started_at") or mtime_iso,
        finished_at=data.get("finished_at") or mtime_iso,
        duration_ms=data.get("duration_ms"),  # type: ignore[arg-type]
        environment=_parse_environment(
            data.get("environment") if isinstance(data.get("environment"), dict) else None
        ),
        telemetry=_parse_telemetry(
            data.get("telemetry") if isinstance(data.get("telemetry"), dict) else None
        ),
        observations=_parse_observations(list(data.get("observations") or [])),
        assertions=_parse_assertions(list(data.get("assertions") or [])),
        judge_results=_parse_judge_results(list(data.get("judge_results") or [])),
        judge_overall_passed=data.get("judge_overall_passed"),
        scores=_parse_scores(list(data.get("scores") or [])),
        summary=EvalSummary.model_validate(summary_raw) if isinstance(summary_raw, dict) else None,
        exploratory_config=(
            EmotionEvalRequest.model_validate(exploratory_raw)
            if isinstance(exploratory_raw, dict)
            else None
        ),
        events=_parse_events(list(data.get("events") or [])),
        error=data.get("error"),  # type: ignore[arg-type]
    )


def load_run(run_id: str, *, base_dir: str | Path | None = None) -> EvalRunResult | None:
    """Load a legacy evaluation result from a persisted record."""

    record = load_run_record(run_id, base_dir=base_dir)
    if record is None:
        return None
    return EvalRunResult(
        run_id=record.run_id,
        scenario_id=record.scenario_id,
        tier=record.tier,
        mode=record.mode,
        status=record.status,
        observations=record.observations,
        assertions=record.assertions,
        judge_results=record.judge_results,
        judge_overall_passed=record.judge_overall_passed,
        error=record.error,
    )


def list_run_summaries(
    *,
    base_dir: str | Path | None = None,
    limit: int = 50,
    tier: str | None = None,
) -> list[dict[str, object]]:
    """List summary rows for persisted evaluation runs."""

    directory = _resolve_runs_dir(base_dir)
    if not directory.exists():
        return []

    paths = sorted(directory.glob("eval_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    summaries: list[dict[str, object]] = []
    for path in paths:
        if len(summaries) >= limit:
            break
        data = json.loads(path.read_text(encoding="utf-8"))
        if tier and data.get("tier") != tier:
            continue
        mtime_iso = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
        finished_at = data.get("finished_at") or mtime_iso
        started_at = data.get("started_at")
        assertions = list(data.get("assertions") or [])
        assertions_passed = all(
            item.get("status") in {"pass", "warn", "skip"} for item in assertions
        ) if assertions else None
        summaries.append(
            {
                "run_id": data.get("run_id", path.stem),
                "scenario_id": data.get("scenario_id", ""),
                "tier": data.get("tier", "smoke"),
                "mode": data.get("mode", "scenario"),
                "status": data.get("status", "failed"),
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_ms": data.get("duration_ms"),
                "assertions_passed": assertions_passed,
                "judge_overall_passed": data.get("judge_overall_passed"),
            }
        )
    return summaries


def persist_record_safe(record: EvalRunRecord, *, base_dir: str | Path | None = None) -> None:
    """Persist a record without raising on I/O failure."""

    try:
        save_run_record(record, base_dir=base_dir)
    except OSError:
        _log.exception("failed to persist eval run: %s", record.run_id)
