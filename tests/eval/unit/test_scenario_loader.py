from pathlib import Path

import pytest

from eval.domain.scenario import (
    ScenarioValidationError,
    iter_scenario_yaml_paths,
    list_scenarios,
    load_scenario,
)
from tests.eval.paths import SCENARIOS_DIR


def test_load_greeting_fixture() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    assert scenario.id == "greeting_01"
    assert scenario.tier == "smoke"
    assert scenario.user_driver.type == "scripted"
    assert len(scenario.user_driver.turns) == 1
    assert scenario.judge is None


def test_load_greeting_fixture_has_tags() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    assert scenario.tags == ["happy_path", "identity_disclosure"]


def test_list_smoke_scenarios() -> None:
    scenarios = list_scenarios(SCENARIOS_DIR / "smoke")
    assert any(item.id == "greeting_01" for item in scenarios)
    assert len(scenarios) == 28
    emotion_smoke = [item for item in scenarios if item.domain == "emotion"]
    assert len(emotion_smoke) == 14


def test_iter_scenario_yaml_paths_scopes_by_tier() -> None:
    smoke_paths = iter_scenario_yaml_paths(SCENARIOS_DIR, tier="smoke")
    judge_paths = iter_scenario_yaml_paths(SCENARIOS_DIR, tier="judge")

    assert smoke_paths
    assert judge_paths
    assert all("smoke" in str(path).replace("\\", "/") for path in smoke_paths)
    assert all("judge" in str(path).replace("\\", "/") for path in judge_paths)
    assert len(smoke_paths) == 28
    assert len(judge_paths) == 15


def test_load_scenario_rejects_invalid_tag(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        """
id: bad_01
domain: emotion
tags: [not_a_tag]
tier: smoke
description: bad
user_driver:
  type: scripted
  turns:
    - text: hi
""",
        encoding="utf-8",
    )
    with pytest.raises(ScenarioValidationError):
        load_scenario(bad)
