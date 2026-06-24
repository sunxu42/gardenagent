from pathlib import Path

import pytest

from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


class _FakeAgent:
    async def respond_with_observation(self, message: str, thread_id: str):
        return f"reply:{message}", None, (), 1.0

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_runner_runs_scripted_scenario() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    result = await EvalRunner(agent_client=_FakeAgent()).run_scenario(scenario)
    assert result.status == "completed"
    assert len(result.observations) == 1
    assert result.observations[0].assistant_text.startswith("reply:")
