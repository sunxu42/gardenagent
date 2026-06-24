from pathlib import Path

import pytest

from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.parametrize(
    "scenario_path",
    sorted(SCENARIOS_DIR / "smoke".glob("*.yaml")),
)
@pytest.mark.asyncio
async def test_smoke_scenario(scenario_path: Path) -> None:
    from eval.application.agent_client import EvalAgentClient

    scenario = load_scenario(scenario_path)
    agent_client = await EvalAgentClient.create()
    result = await EvalRunner(agent_client=agent_client).run_scenario(scenario)
    assert result.status == "completed", result.assertions
