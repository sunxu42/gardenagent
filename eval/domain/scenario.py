from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from shared.config.paths import resolve_eval_scenarios_dir

EvalTier = Literal["smoke", "judge", "exploratory"]
UserDriverType = Literal["scripted", "simulated"]


class UserTurn(BaseModel):
    text: str = Field(min_length=1)


class UserDriverConfig(BaseModel):
    type: UserDriverType
    turns: list[UserTurn] = Field(default_factory=list)


class AssertionConfig(BaseModel):
    type: str
    name: str
    forbidden: list[str] = Field(default_factory=list)
    required: list[str] = Field(default_factory=list)
    min_chars: int | None = None
    allowed: list[str] = Field(default_factory=list)
    any_round: bool = False
    tool_name: str | None = None
    optional: bool = False


class JudgePolicyConfig(BaseModel):
    blocking: list[str] = Field(default_factory=list)
    min_overall: float = 0.0


class JudgeConfig(BaseModel):
    enabled: bool = False
    metrics: list[str] = Field(default_factory=list)
    policy: JudgePolicyConfig = Field(default_factory=JudgePolicyConfig)


class ScenarioSetup(BaseModel):
    rounds: int = Field(default=1, ge=1, le=8)


class ScenarioFixture(BaseModel):
    id: str
    domain: str
    tier: EvalTier = "smoke"
    description: str = ""
    setup: ScenarioSetup = Field(default_factory=ScenarioSetup)
    user_driver: UserDriverConfig
    assertions: list[AssertionConfig] = Field(default_factory=list)
    judge: JudgeConfig | None = None


def load_scenario(path: Path) -> ScenarioFixture:
    """Load one scenario fixture from a YAML file."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ScenarioFixture.model_validate(data)


def list_scenarios(directory: Path) -> list[ScenarioFixture]:
    """Load all scenario fixtures under a directory."""

    paths = sorted(directory.glob("**/*.yaml"))
    return [load_scenario(path) for path in paths]


def resolve_scenario_by_id(
    scenario_id: str,
    root: Path | None = None,
) -> ScenarioFixture:
    """Resolve a scenario fixture by id or nested path."""

    scenario_root = root or resolve_eval_scenarios_dir()
    normalized = scenario_id.replace("\\", "/").strip("/")
    direct = scenario_root / f"{normalized}.yaml"
    if direct.is_file():
        return load_scenario(direct)
    nested = scenario_root / normalized
    if nested.is_file():
        return load_scenario(nested)
    raise FileNotFoundError(f"scenario not found: {scenario_id}")
