"""Manifest module specs (PromptModule) and load_manifest()."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

TIER_ORDER = ("stable", "semi_stable", "volatile")


@dataclass
class PromptModule:
    id: str
    tier: str
    priority: int
    renderer: str | None = None
    source: str | None = None
    slice: str | list[str] | None = None
    when: str | None = None
    always: bool = False


def _parse_module(raw: dict[str, Any]) -> PromptModule:
    return PromptModule(
        id=str(raw["id"]),
        tier=str(raw.get("tier") or "volatile"),
        priority=int(raw.get("priority") or 0),
        renderer=str(raw["renderer"]) if raw.get("renderer") else None,
        source=str(raw["source"]) if raw.get("source") else None,
        slice=raw.get("slice"),
        when=str(raw["when"]) if raw.get("when") is not None else None,
        always=bool(raw.get("always", False)),
    )


def load_manifest(path: str | Path) -> list[PromptModule]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    modules = data.get("modules")
    if not isinstance(modules, list):
        return []
    out: list[PromptModule] = []
    for item in modules:
        if isinstance(item, dict) and item.get("id"):
            out.append(_parse_module(item))
    return out
