from eval.domain.judge.metrics_registry import (
    JUDGE_REASON_LANGUAGE_RULE,
    JUDGE_REASON_LANGUAGE_STEP,
    load_metric_ref,
)


def test_load_empathy_metric() -> None:
    definition = load_metric_ref("emotion_support.empathy")
    assert definition.name == "empathy"
    assert definition.threshold == 0.65
    assert definition.blocking is False
    assert len(definition.evaluation_steps) >= 3


def test_load_boundary_safety_metric() -> None:
    definition = load_metric_ref("emotion_support.boundary_safety")
    assert definition.blocking is True
    assert definition.evaluation_steps


def test_build_conversational_geval_sets_evaluation_params(monkeypatch) -> None:
    from unittest.mock import MagicMock

    from deepeval.test_case import MultiTurnParams

    from eval.domain.judge.metrics_registry import build_conversational_geval

    captured: dict[str, object] = {}

    def _fake_geval(**kwargs: object) -> MagicMock:
        captured.update(kwargs)
        metric = MagicMock()
        metric.evaluation_params = kwargs["evaluation_params"]
        return metric

    monkeypatch.setattr(
        "deepeval.metrics.ConversationalGEval",
        _fake_geval,
    )

    definition = load_metric_ref("emotion_support.empathy")
    metric = build_conversational_geval(definition, model="gpt-4")
    params = captured["evaluation_params"]
    assert MultiTurnParams.CONTENT in params
    assert MultiTurnParams.ROLE in params
    assert captured["async_mode"] is False
    assert JUDGE_REASON_LANGUAGE_RULE in str(captured["criteria"])
    assert JUDGE_REASON_LANGUAGE_STEP in captured["evaluation_steps"]
    assert metric.evaluation_params == params
