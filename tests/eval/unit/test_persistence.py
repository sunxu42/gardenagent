import json
from pathlib import Path

from eval.api.schemas import AgentAffectSnapshot
from eval.domain.models import EvalRunResult, TurnObservation
from eval.infrastructure.persistence import load_run_record, save_run, save_run_record
from eval.infrastructure.record import EvalRunRecord, RunEnvironment, RunTelemetry


def test_save_run_writes_json(tmp_path: Path) -> None:
    result = EvalRunResult(
        run_id="run_test",
        scenario_id="greeting_01",
        tier="smoke",
        mode="scenario",
        status="completed",
        observations=(),
    )
    path = save_run(result, base_dir=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run_test"
    assert payload["scenario_id"] == "greeting_01"
    assert payload["schema_version"] == 0


def test_save_run_serializes_agent_affect_snapshot(tmp_path: Path) -> None:
    result = EvalRunResult(
        run_id="run_affect",
        scenario_id="greeting_01",
        tier="smoke",
        mode="scenario",
        status="completed",
        observations=(
            TurnObservation(
                round=1,
                user_text="你好",
                assistant_text="你好呀",
                agent_affect=AgentAffectSnapshot(emotion="calm", relationship_stage="friend"),
            ),
        ),
    )
    path = save_run(result, base_dir=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["observations"][0]["agent_affect"] == {
        "emotion": "calm",
        "vad": None,
        "relationship_stage": "friend",
    }


def test_save_run_record_round_trip(tmp_path: Path) -> None:
    record = EvalRunRecord(
        run_id="eval_v1",
        mode="exploratory",
        tier="exploratory",
        status="completed",
        scenario_id="exploratory",
        started_at="2026-06-23T10:00:00+00:00",
        finished_at="2026-06-23T10:01:00+00:00",
        duration_ms=60000,
        environment=RunEnvironment(git_commit="abc123"),
        telemetry=RunTelemetry(agent_cold_start=True, agent_reused=False),
    )
    save_run_record(record, base_dir=tmp_path)
    loaded = load_run_record("eval_v1", base_dir=tmp_path)
    assert loaded is not None
    assert loaded.schema_version == 1
    assert loaded.telemetry.agent_cold_start is True


def test_load_run_record_v0_compat(tmp_path: Path) -> None:
    path = tmp_path / "eval_legacy.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "eval_legacy",
                "scenario_id": "greeting_01",
                "tier": "smoke",
                "mode": "scenario",
                "status": "completed",
                "observations": [],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_run_record("eval_legacy", base_dir=tmp_path)
    assert loaded is not None
    assert loaded.schema_version == 0
    assert loaded.events == ()


def test_list_run_summaries_includes_mode(tmp_path: Path) -> None:
    from eval.infrastructure.persistence import list_run_summaries

    save_run_record(
        EvalRunRecord(
            run_id="eval_explore",
            mode="exploratory",
            tier="exploratory",
            status="completed",
            scenario_id="exploratory",
            duration_ms=1200,
        ),
        base_dir=tmp_path,
    )
    summaries = list_run_summaries(base_dir=tmp_path, tier="exploratory")
    assert len(summaries) == 1
    assert summaries[0]["mode"] == "exploratory"
    assert summaries[0]["duration_ms"] == 1200
