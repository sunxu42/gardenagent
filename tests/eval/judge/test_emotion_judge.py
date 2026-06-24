from pathlib import Path

import pytest

from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


@pytest.mark.judge
@pytest.mark.integration
@pytest.mark.parametrize(
    "scenario_path",
    sorted(SCENARIOS_DIR / "judge".glob("*.yaml")),
)
@pytest.mark.asyncio
async def test_judge_scenario(scenario_path: Path) -> None:
    from eval.application.agent_client import EvalAgentClient
    from eval.domain.judge.model_factory import build_eval_model
    from eval.domain.judge.runner import JudgeRunner
    from shared.config.resolve_agent import resolve_agent_runtime
    from agent.configs.secrets import load_secrets
    from shared.config.agent import load_agent_settings

    scenario = load_scenario(scenario_path)
    config = resolve_agent_runtime(load_agent_settings(), load_secrets())
    agent_client = await EvalAgentClient.create()
    judge_runner = JudgeRunner(build_eval_model(config))
    result = await EvalRunner(
        agent_client=agent_client,
        judge_runner=judge_runner,
    ).run_scenario(scenario)
    assert result.assertions_all_passed, result.assertions
    assert result.judge_overall_passed is True, result.judge_results
