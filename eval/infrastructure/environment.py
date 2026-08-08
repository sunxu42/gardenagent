from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from shared.config.agent import Config

from eval.infrastructure.record import RunEnvironment

from shared.config.paths import resolve_prompts_dir


def capture_run_environment(*, config: Config | None) -> RunEnvironment:
    """Capture a best-effort environment fingerprint for one eval run."""

    agent_model: str | None = None
    eval_judge_model: str | None = None
    if config is not None:
        agent_model = config.llm_model_name
        eval_judge_model = config.eval_llm_model
    return RunEnvironment(
        git_commit=_git_commit(),
        git_dirty=_git_dirty(),
        agent_model=agent_model,
        eval_judge_model=eval_judge_model,
        prompt_manifest_hash=_manifest_hash(),
        python_version=sys.version.split()[0],
    )


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value[:12] if value else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_dirty() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode != 0:
            return None
        return bool(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return None


def _manifest_hash() -> str | None:
    manifest_path = resolve_prompts_dir() / "manifest.yaml"
    try:
        if not manifest_path.is_file():
            return None
        digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        return digest[:12]
    except OSError:
        return None
