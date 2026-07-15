"""Shared L0 assertion snippets for eval scenarios.

Scenarios reference these by name via ``assertion_sets``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from shared.config.paths import EVAL_FIXTURES_DIR

_SNIPPETS_DIR = EVAL_FIXTURES_DIR / "snippets"


@lru_cache(maxsize=1)
def _load_all_snippets() -> dict[str, list[dict[str, Any]]]:
    if not _SNIPPETS_DIR.is_dir():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(_SNIPPETS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        assertions = data.get("assertions")
        if isinstance(assertions, list):
            out[path.stem] = [item for item in assertions if isinstance(item, dict)]
    return out


def expand_assertion_sets(
    assertion_sets: list[str] | None,
    assertions: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Expand named assertion sets, then append scenario-local assertions."""
    snippets = _load_all_snippets()
    merged: list[dict[str, Any]] = []
    for name in assertion_sets or []:
        key = str(name).strip()
        if not key:
            continue
        if key not in snippets:
            raise KeyError(f"unknown assertion_set: {key}")
        merged.extend(snippets[key])
    if assertions:
        merged.extend(assertions)
    return merged


def clear_snippet_cache() -> None:
    """Test helper to reload snippets after writing temp files."""
    _load_all_snippets.cache_clear()
