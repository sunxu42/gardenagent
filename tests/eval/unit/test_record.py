from datetime import UTC, datetime

from eval.domain.progress import EvalProgressEvent
from eval.infrastructure.record import EvalRunRecord, RunEnvironment
from eval.infrastructure.recorder import EVENT_CAP, RunRecorder


def test_eval_run_record_defaults() -> None:
    record = EvalRunRecord(
        run_id="eval_test",
        mode="scenario",
        tier="smoke",
        status="completed",
        scenario_id="greeting_01",
    )
    assert record.schema_version == 1
    assert record.events == ()
    assert record.environment.git_commit is None


def test_recorder_records_events_with_timestamp() -> None:
    recorder = RunRecorder(
        run_id="eval_r1",
        mode="scenario",
        tier="smoke",
        scenario_id="greeting_01",
        environment=RunEnvironment(),
        started_at=datetime(2026, 6, 23, 10, 0, 0, tzinfo=UTC),
    )
    recorder.record(
        EvalProgressEvent(type="eval_progress", run_id="eval_r1", payload={"message": "hi"})
    )
    record = recorder.build(status="completed", observations=())
    assert len(record.events) == 1
    assert record.events[0].type == "eval_progress"
    assert record.events[0].at


def test_recorder_caps_events_at_80() -> None:
    recorder = RunRecorder(
        run_id="eval_cap",
        mode="scenario",
        tier="smoke",
        scenario_id="x",
        environment=RunEnvironment(),
        started_at=datetime.now(tz=UTC),
    )
    for index in range(EVENT_CAP + 5):
        recorder.record(
            EvalProgressEvent(
                type="eval_progress",
                run_id="eval_cap",
                payload={"index": index},
            )
        )
    record = recorder.build(status="completed", observations=())
    assert len(record.events) == EVENT_CAP
    assert record.events[-1].payload["index"] == EVENT_CAP + 4
