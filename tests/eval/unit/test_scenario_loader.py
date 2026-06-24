from pathlib import Path

from eval.domain.scenario import list_scenarios, load_scenario
from tests.eval.paths import SCENARIOS_DIR


def test_load_greeting_fixture() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    assert scenario.id == "greeting_01"
    assert scenario.tier == "smoke"
    assert scenario.user_driver.type == "scripted"
    assert len(scenario.user_driver.turns) == 1
    assert scenario.judge is None


def test_list_smoke_scenarios() -> None:
    scenarios = list_scenarios(SCENARIOS_DIR / "smoke")
    assert any(item.id == "greeting_01" for item in scenarios)
    assert len(scenarios) == 10
