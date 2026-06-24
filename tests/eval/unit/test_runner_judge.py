from pathlib import Path
from unittest.mock import MagicMock

import pytest

from eval.domain.judge.runner import JudgeRunner
from eval.domain.models import JudgeMetricResult
from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


class _FakeAgent:
    async def respond_with_observation(self, message: str, thread_id: str):
        return f"reply:{message}", None, (), 1.0

    async def aclose(self) -> None:
        return None


class _FakeJudgeRunner(JudgeRunner):
    def __init__(self) -> None:
        super().__init__(model=MagicMock())

    async def a_evaluate(
        self,
        observations,
        judge_config,
        metric_definitions,
        *,
        scenario_description=None,
        on_metric_done=None,
        cancel_check=None,
    ):
        return (
            JudgeMetricResult(
                name="empathy",
                score=0.8,
                passed=True,
                threshold=0.65,
                reason="ok",
            ),
        )


@pytest.mark.asyncio
async def test_runner_invokes_judge_when_enabled(tmp_path: Path) -> None:
    scenario = load_scenario(SCENARIOS_DIR / "judge/emotion_anxious_01.yaml")
    result = await EvalRunner(
        agent_client=_FakeAgent(),
        judge_runner=_FakeJudgeRunner(),
    ).run_scenario(scenario)
    assert result.judge_results
    assert result.judge_overall_passed is True
