"""Repository, data, and runtime path constants."""

from __future__ import annotations

import os
from pathlib import Path

# Repo root: shared/config/paths.py → shared/config → shared → repo
REPO_ROOT = Path(__file__).resolve().parents[2]

CWD = os.getcwd()
ENV_FILE = os.path.join(CWD, ".env")
CONFIG_FILE = os.path.join(CWD, ".config.yaml")

DATA_DIR = REPO_ROOT / "data"
RUNTIME_DIR = REPO_ROOT / "runtime"

PROMPTS_DIR = DATA_DIR / "prompts"
WORKSPACE_DIR = RUNTIME_DIR / "workspace"
EVAL_RUNS_DIR = RUNTIME_DIR / "eval_runs"
EVAL_FIXTURES_DIR = DATA_DIR / "eval_fixtures"
EVAL_SCENARIOS_DIR = EVAL_FIXTURES_DIR / "scenarios"
EVAL_METRICS_DIR = EVAL_FIXTURES_DIR / "metrics"
EVAL_TAXONOMY_FILE = EVAL_FIXTURES_DIR / "taxonomy.yaml"
AGENT_CONFIGS_DIR = DATA_DIR / "agent_configs"
REFERENCE_DIR = DATA_DIR / "reference"
REFERENCE_SKILLS_DIR = REFERENCE_DIR / "skills"

# Default relative paths (for .config.yaml / Config model)
DEFAULT_PROMPTS_DIR = "data/prompts"
DEFAULT_WORKSPACE_DIR = "runtime/workspace"
DEFAULT_SUBAGENTS_YAML = "data/agent_configs/subagents.yaml"
DEFAULT_MCP_SERVERS_YAML = "data/agent_configs/mcp_servers.yaml"
DEFAULT_EMOTION_STATE_PATH = "runtime/workspace/emotion/emotion_state.json"

_LEGACY_PROMPTS_DIR = REPO_ROOT / "yard" / "prompts"
_LEGACY_WORKSPACE_DIR = REPO_ROOT / "yard" / "workspace"
_LEGACY_EVAL_RUNS_DIR = REPO_ROOT / "eval_runs"
_LEGACY_EVAL_FIXTURES_DIR = REPO_ROOT / "eval_fixtures"
_LEGACY_REFERENCE_DIR = REPO_ROOT / "yard" / "reference"


def _resolve_existing(primary: Path, legacy: Path) -> Path:
    if primary.exists():
        return primary
    if legacy.exists():
        return legacy
    return primary


def resolve_prompts_dir() -> Path:
    """Return prompts directory (prefers ``data/prompts``)."""

    return _resolve_existing(PROMPTS_DIR, _LEGACY_PROMPTS_DIR)


def resolve_workspace_dir() -> Path:
    """Return workspace directory (prefers ``runtime/workspace``)."""

    return _resolve_existing(WORKSPACE_DIR, _LEGACY_WORKSPACE_DIR)


def resolve_eval_runs_dir() -> Path:
    """Return eval run artifacts directory."""

    return _resolve_existing(EVAL_RUNS_DIR, _LEGACY_EVAL_RUNS_DIR)


def resolve_eval_scenarios_dir() -> Path:
    """Return scenario fixture root."""

    primary = EVAL_SCENARIOS_DIR
    legacy = _LEGACY_EVAL_FIXTURES_DIR / "scenarios"
    return _resolve_existing(primary, legacy)


def resolve_eval_metrics_dir() -> Path:
    """Return judge metric YAML root."""

    primary = EVAL_METRICS_DIR
    legacy = _LEGACY_EVAL_FIXTURES_DIR / "metrics"
    return _resolve_existing(primary, legacy)


def resolve_eval_taxonomy_path() -> Path:
    """Return taxonomy YAML path."""

    primary = EVAL_TAXONOMY_FILE
    legacy = _LEGACY_EVAL_FIXTURES_DIR / "taxonomy.yaml"
    if primary.is_file():
        return primary
    if legacy.is_file():
        return legacy
    return primary


def resolve_reference_dir() -> Path:
    """Return reference seed templates directory."""

    return _resolve_existing(REFERENCE_DIR, _LEGACY_REFERENCE_DIR)


def repo_relative(path: str | Path) -> Path:
    """Resolve a config path relative to repo root when not absolute."""

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (REPO_ROOT / candidate).resolve()
