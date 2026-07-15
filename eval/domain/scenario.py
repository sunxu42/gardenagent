from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

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
    max_chars: int | None = None
    allowed: list[str] = Field(default_factory=list)
    any_round: bool = False
    tool_name: str | None = None
    optional: bool = False
    pattern: str | None = None


class JudgePolicyConfig(BaseModel):
    blocking: list[str] = Field(default_factory=list)
    min_overall: float = 0.0


class JudgeConfig(BaseModel):
    enabled: bool = False
    metrics: list[str] = Field(default_factory=list)
    policy: JudgePolicyConfig = Field(default_factory=JudgePolicyConfig)


class ScenarioSetup(BaseModel):
    rounds: int = Field(default=1, ge=1, le=8)
    session_reset_after_round: int | None = Field(default=None, ge=1, le=7)


class ScenarioValidationError(ValueError):
    """Raised when a scenario fixture fails taxonomy validation."""


# Renamed stems: keep old public ids resolving for history / bookmarks.
_LEGACY_PUBLIC_IDS: dict[str, str] = {
    "smoke/a2ui_agent_binary": "smoke/a2ui_agent_init_binary",
    "smoke/a2ui_agent_game_pick": "smoke/a2ui_agent_init_game_pick",
    "smoke/a2ui_agent_puzzle_branch": "smoke/a2ui_agent_init_puzzle_branch",
    "smoke/a2ui_agent_table_compare": "smoke/a2ui_agent_init_table_compare",
    "smoke/a2ui_binary": "smoke/a2ui_user_binary",
    "smoke/a2ui_emoji": "smoke/a2ui_user_emoji",
    "smoke/a2ui_info": "smoke/a2ui_negative_explain_ok",
    "smoke/a2ui_list_typhoon_timeline": "smoke/a2ui_user_structured_list_typhoon",
    "smoke/a2ui_multi": "smoke/a2ui_user_multi_select",
    "smoke/a2ui_negative": "smoke/a2ui_negative_plain_qa",
    "smoke/a2ui_plan_3": "smoke/a2ui_user_single_select_plans",
    "smoke/a2ui_table_readonly": "smoke/a2ui_user_table_readonly",
    "smoke/a2ui_table_select": "smoke/a2ui_user_table_select",
    "judge/persona_warmth_judge_01": "judge/persona_warmth_comfort_01",
}


def scenario_public_id(path: Path, root: Path) -> str:
    """Stable API id: ``{tier}/{stem}`` for ``.../{domain}/{tier}/{stem}.yaml``."""
    rel = path.resolve().relative_to(root.resolve())
    parts = rel.parts
    if len(parts) >= 2 and parts[-2] in {"smoke", "judge", "exploratory"}:
        return f"{parts[-2]}/{path.stem}"
    return str(rel).replace("\\", "/").removesuffix(".yaml")


def iter_scenario_yaml_paths(root: Path, tier: str | None = None) -> list[Path]:
    """List scenario YAML paths, optionally scoped to one tier directory name."""

    if tier in {"smoke", "judge", "exploratory"}:
        return sorted(
            path for path in root.glob(f"**/{tier}/*.yaml") if path.is_file()
        )

    return sorted(path for path in root.glob("**/*.yaml") if path.is_file())


def find_scenario_path(scenario_id: str, root: Path) -> Path:
    """Resolve a public id or relative path to a concrete YAML file."""
    normalized = scenario_id.replace("\\", "/").strip("/")
    normalized = _LEGACY_PUBLIC_IDS.get(normalized, normalized)

    direct = root / f"{normalized}.yaml"
    if direct.is_file():
        return direct

    nested = root / normalized
    if nested.is_file():
        return nested

    if "/" in normalized:
        tier, stem = normalized.split("/", 1)
        if tier in {"smoke", "judge", "exploratory"} and "/" not in stem:
            matches = sorted(root.glob(f"**/{tier}/{stem}.yaml"))
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise FileNotFoundError(
                    f"ambiguous scenario id {scenario_id!r}: {[str(m) for m in matches]}"
                )

    raise FileNotFoundError(f"scenario not found: {scenario_id}")


def _merge_user_driver(base_ud: dict[str, Any], child_ud: dict[str, Any] | None) -> dict[str, Any]:
    if child_ud is None:
        return dict(base_ud)
    append = child_ud.get("turns_append")
    if append is not None:
        base_turns = list(base_ud.get("turns") or [])
        return {
            "type": child_ud.get("type") or base_ud.get("type") or "scripted",
            "turns": base_turns + list(append),
        }
    if "turns" in child_ud:
        return {
            "type": child_ud.get("type") or base_ud.get("type") or "scripted",
            "turns": child_ud["turns"],
        }
    merged = {**base_ud, **child_ud}
    merged.pop("turns_append", None)
    return merged


def merge_scenario_dicts(base: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Merge a child scenario onto its ``extends`` base.

    Assertions are replaced by the child when it declares ``assertions`` or
    ``assertion_sets`` (judge suites should not inherit full smoke L0 contracts).
    User turns can be extended via ``user_driver.turns_append``.
    """
    result: dict[str, Any] = {**base}

    for key in ("id", "tier", "description", "tags", "judge", "domain"):
        if key in child:
            result[key] = child[key]

    if "setup" in child:
        result["setup"] = {**(base.get("setup") or {}), **(child.get("setup") or {})}

    result["user_driver"] = _merge_user_driver(
        dict(base.get("user_driver") or {}),
        child.get("user_driver") if isinstance(child.get("user_driver"), dict) else None,
    )

    if "assertions" in child or "assertion_sets" in child:
        if "assertion_sets" in child:
            result["assertion_sets"] = child["assertion_sets"]
        else:
            result.pop("assertion_sets", None)
        result["assertions"] = child.get("assertions") or []
    return result


def load_scenario_dict(
    path: Path,
    *,
    root: Path | None = None,
    _stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Load raw scenario YAML, recursively applying ``extends``."""
    scenario_root = root or resolve_eval_scenarios_dir()
    public_id = scenario_public_id(path, scenario_root)
    if public_id in _stack:
        cycle = " -> ".join([*_stack, public_id])
        raise ScenarioValidationError(f"scenario extends cycle: {cycle}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ScenarioValidationError(f"scenario must be a mapping: {path}")

    extends = raw.get("extends")
    if not extends:
        data = dict(raw)
        data.pop("extends", None)
        return data

    base_id = str(extends).strip()
    base_path = find_scenario_path(base_id, scenario_root)
    base = load_scenario_dict(
        base_path,
        root=scenario_root,
        _stack=(*_stack, public_id),
    )
    child = dict(raw)
    child.pop("extends", None)
    return merge_scenario_dicts(base, child)


class ScenarioFixture(BaseModel):
    id: str
    domain: str
    tags: list[str] = Field(default_factory=list)
    tier: EvalTier = "smoke"
    description: str = ""
    setup: ScenarioSetup = Field(default_factory=ScenarioSetup)
    user_driver: UserDriverConfig
    assertion_sets: list[str] = Field(default_factory=list)
    assertions: list[AssertionConfig] = Field(default_factory=list)
    judge: JudgeConfig | None = None

    @model_validator(mode="before")
    @classmethod
    def _expand_assertion_sets(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        from eval.domain.snippets import expand_assertion_sets

        raw_assertions = data.get("assertions")
        sets = data.get("assertion_sets")
        if not sets and not isinstance(raw_assertions, list):
            return data
        try:
            merged = expand_assertion_sets(
                list(sets) if isinstance(sets, list) else None,
                list(raw_assertions) if isinstance(raw_assertions, list) else None,
            )
        except KeyError as exc:
            raise ScenarioValidationError(str(exc)) from exc
        return {**data, "assertions": merged, "assertion_sets": []}


def load_scenario(path: Path, *, validate: bool = True, root: Path | None = None) -> ScenarioFixture:
    """Load one scenario fixture from a YAML file."""

    scenario_root = root or resolve_eval_scenarios_dir()
    # When loading from tmp_path in tests, use the file's parent tree if outside fixtures.
    try:
        path.resolve().relative_to(scenario_root.resolve())
        data = load_scenario_dict(path, root=scenario_root)
    except ValueError:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ScenarioValidationError(f"scenario must be a mapping: {path}") from None
        if data.get("extends"):
            # Allow extends against real fixtures even from a temp child file.
            data = merge_scenario_dicts(
                load_scenario_dict(
                    find_scenario_path(str(data["extends"]), scenario_root),
                    root=scenario_root,
                ),
                {k: v for k, v in data.items() if k != "extends"},
            )

    scenario = ScenarioFixture.model_validate(data)
    if validate:
        from eval.domain.taxonomy import get_taxonomy_registry

        registry = get_taxonomy_registry()
        try:
            registry.validate_scenario(domain=scenario.domain, tags=scenario.tags)
        except ValueError as exc:
            raise ScenarioValidationError(str(exc)) from exc
    return scenario


def list_scenarios(directory: Path) -> list[ScenarioFixture]:
    """Load all scenario fixtures under a directory."""

    return [load_scenario(path) for path in iter_scenario_yaml_paths(directory)]


def list_scenarios_with_paths(root: Path | None = None) -> list[tuple[str, ScenarioFixture]]:
    """Load all scenario fixtures with stable ``{tier}/{stem}`` ids."""

    scenario_root = root or resolve_eval_scenarios_dir()
    items: list[tuple[str, ScenarioFixture]] = []
    for path in iter_scenario_yaml_paths(scenario_root):
        public_id = scenario_public_id(path, scenario_root)
        items.append((public_id, load_scenario(path, root=scenario_root)))
    return items


def resolve_scenario_by_id(
    scenario_id: str,
    root: Path | None = None,
) -> ScenarioFixture:
    """Resolve a scenario by public id (``smoke/foo``) or nested path."""

    scenario_root = root or resolve_eval_scenarios_dir()
    path = find_scenario_path(scenario_id, scenario_root)
    return load_scenario(path, root=scenario_root)
