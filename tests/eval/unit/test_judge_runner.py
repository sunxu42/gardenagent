from unittest.mock import MagicMock, patch

from eval.domain.judge.runner import JudgeRunner
from eval.domain.models import TurnObservation
from eval.domain.scenario import JudgeConfig


def test_judge_runner_evaluates_metrics_sequentially() -> None:
    observations = (
        TurnObservation(
            round=1,
            user_text="hello",
            assistant_text="hi there",
            tool_events=(),
            agent_affect=None,
            latency_ms=None,
            raw_updates=(),
        ),
    )
    metric_a = MagicMock()
    metric_a.score = 0.8
    metric_a.reason = "good"
    metric_b = MagicMock()
    metric_b.score = 0.7
    metric_b.reason = "ok"

    definitions = (
        MagicMock(name="empathy", threshold=0.65, blocking=False),
        MagicMock(name="supportive_tone", threshold=0.60, blocking=False),
    )

    with (
        patch(
            "eval.domain.judge.runner.build_conversational_geval",
            side_effect=[metric_a, metric_b],
        ),
        patch("eval.domain.judge.runner.time.sleep") as sleep_mock,
    ):
        results = JudgeRunner(model=MagicMock()).evaluate(
            observations,
            JudgeConfig(enabled=True, metrics=["emotion_support.empathy"]),
            definitions,
            scenario_description="test",
        )

    assert len(results) == 2
    assert metric_a.measure.call_count == 1
    assert metric_b.measure.call_count == 1
    sleep_mock.assert_called_once()
