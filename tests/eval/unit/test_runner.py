from pathlib import Path

import pytest

from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


class _FakeAgent:
    def __init__(self) -> None:
        self.thread_ids: list[str] = []

    async def respond_with_observation(self, message: str, thread_id: str):
        self.thread_ids.append(thread_id)
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


@pytest.mark.asyncio
async def test_runner_resets_thread_after_configured_round(tmp_path: Path) -> None:
    scenario_path = tmp_path / "reset.yaml"
    scenario_path.write_text(
        """
id: reset_01
domain: memory
tags: [cross_session, memory_recall]
tier: smoke
description: reset thread
setup:
  rounds: 2
  session_reset_after_round: 1
user_driver:
  type: scripted
  turns:
    - text: "请记住我喜欢玫瑰。"
    - text: "我喜欢什么花？"
assertions:
  - type: assistant_min_length
    name: reply
    min_chars: 1
""",
        encoding="utf-8",
    )
    scenario = load_scenario(scenario_path)
    agent = _FakeAgent()
    await EvalRunner(agent_client=agent).run_scenario(scenario)
    assert len(agent.thread_ids) == 2
    assert agent.thread_ids[0] != agent.thread_ids[1]
