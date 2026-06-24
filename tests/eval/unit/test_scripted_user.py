from pathlib import Path

import pytest

from eval.domain.scenario import load_scenario
from eval.domain.users.scripted_user import ScriptedUser
from tests.eval.paths import SCENARIOS_DIR


@pytest.mark.asyncio
async def test_scripted_user_returns_turns_in_order() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    user = ScriptedUser(scenario.user_driver)
    text = await user.generate_turn(scenario, [], 1)
    assert "你是谁" in text
    with pytest.raises(IndexError):
        await user.generate_turn(scenario, [], 2)
