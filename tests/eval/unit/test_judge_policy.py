from eval.domain.judge.policy import evaluate_policy
from eval.domain.models import JudgeMetricResult
from eval.domain.scenario import JudgePolicyConfig


def test_policy_fails_on_blocking_metric() -> None:
    results = (
        JudgeMetricResult(
            name="empathy",
            score=0.9,
            passed=True,
            threshold=0.65,
            reason="ok",
        ),
        JudgeMetricResult(
            name="boundary_safety",
            score=0.5,
            passed=False,
            threshold=0.7,
            reason="unsafe",
            blocking=True,
        ),
    )
    policy = JudgePolicyConfig(blocking=["boundary_safety"], min_overall=0.6)
    assert evaluate_policy(results, policy) is False


def test_policy_passes_when_overall_and_blocking_ok() -> None:
    results = (
        JudgeMetricResult(
            name="empathy",
            score=0.8,
            passed=True,
            threshold=0.65,
            reason="ok",
        ),
        JudgeMetricResult(
            name="boundary_safety",
            score=0.75,
            passed=True,
            threshold=0.7,
            reason="ok",
            blocking=True,
        ),
    )
    policy = JudgePolicyConfig(blocking=["boundary_safety"], min_overall=0.7)
    assert evaluate_policy(results, policy) is True
