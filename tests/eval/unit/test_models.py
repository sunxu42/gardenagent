from eval.domain.models import (
    AssertionResult,
    AssertionStatus,
    EvalRunResult,
    TurnObservation,
)


def test_turn_observation_defaults() -> None:
    obs = TurnObservation(round=1, user_text="hi", assistant_text="hello")
    assert obs.tool_events == ()
    assert obs.agent_affect is None
    assert obs.latency_ms is None


def test_eval_run_result_failed_when_assertion_fails() -> None:
    result = EvalRunResult(
        run_id="r1",
        scenario_id="greeting_01",
        tier="smoke",
        mode="scenario",
        status="failed",
        observations=(),
        assertions=(
            AssertionResult(
                name="no_ai",
                status=AssertionStatus.FAIL,
                message="forbidden word found",
            ),
        ),
    )
    assert result.assertions_all_passed is False


def test_eval_run_result_accepts_cancelled_status() -> None:
    result = EvalRunResult(
        run_id="eval_x",
        scenario_id="greeting_01",
        tier="smoke",
        mode="scenario",
        status="cancelled",
        observations=(),
    )
    assert result.status == "cancelled"
