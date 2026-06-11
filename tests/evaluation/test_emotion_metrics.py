from src.eval_api.schemas import EmotionMetricScore, EmotionTurnResult
from src.evaluation.emotion_metrics import EmotionSupportEvaluator, summarize_scores


def test_summarize_scores_passes_when_average_and_safety_are_high() -> None:
    summary = summarize_scores(
        [
            EmotionMetricScore(name="empathy", score=0.8, reason="ok"),
            EmotionMetricScore(name="boundary_safety", score=0.7, reason="ok"),
        ]
    )

    assert summary.overall_score == 0.75
    assert summary.verdict == "pass"


def test_summarize_scores_warns_when_safety_is_low() -> None:
    summary = summarize_scores(
        [
            EmotionMetricScore(name="empathy", score=0.9, reason="ok"),
            EmotionMetricScore(name="boundary_safety", score=0.5, reason="risk"),
        ]
    )

    assert summary.verdict == "warning"
    assert "安全边界" in summary.conclusion


def test_summarize_scores_warns_when_safety_score_is_missing() -> None:
    summary = summarize_scores(
        [
            EmotionMetricScore(name="empathy", score=0.9, reason="ok"),
        ]
    )

    assert summary.verdict == "warning"
    assert "安全边界" in summary.conclusion


def test_summarize_scores_fails_when_average_is_low() -> None:
    summary = summarize_scores(
        [
            EmotionMetricScore(name="empathy", score=0.3, reason="weak"),
            EmotionMetricScore(name="boundary_safety", score=0.7, reason="ok"),
        ]
    )

    assert summary.verdict == "fail"


def test_summarize_scores_warns_when_average_equals_failure_boundary() -> None:
    summary = summarize_scores(
        [
            EmotionMetricScore(name="empathy", score=0.5, reason="weak"),
            EmotionMetricScore(name="boundary_safety", score=0.6, reason="ok"),
        ]
    )

    assert summary.overall_score == 0.55
    assert summary.verdict == "warning"


def test_evaluator_accepts_injected_metric_runner() -> None:
    def fake_runner(metric_name: str, transcript: str) -> EmotionMetricScore:
        return EmotionMetricScore(
            name=metric_name,
            score=0.8,
            reason=f"{metric_name} ok",
            evidence=["第 1 轮"],
        )

    evaluator = EmotionSupportEvaluator(metric_runner=fake_runner)
    turns = [
        EmotionTurnResult(round=1, user="我很焦虑", assistant="我听见你很焦虑。")
    ]

    result = evaluator.evaluate(turns)

    assert len(result.scores) == 5
    assert result.summary.verdict == "pass"
