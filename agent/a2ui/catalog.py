"""Load A2UI template catalog entries and sample variant params."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CATALOG_DIR = Path(__file__).resolve().parent / "catalog"


def list_templates() -> list[dict[str, Any]]:
    """Return all template catalog entries sorted by filename."""
    templates: list[dict[str, Any]] = []
    for path in sorted(_CATALOG_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            templates.append(json.load(handle))
    return templates


def get_template(template_id: str) -> dict[str, Any]:
    """Load one template catalog entry by id."""
    path = _CATALOG_DIR / f"{template_id}.json"
    if not path.is_file():
        raise KeyError(f"unknown template: {template_id}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_variant_params(template_id: str, variant_id: str) -> dict[str, Any]:
    """Return params for a catalog sample variant."""
    template = get_template(template_id)
    for variant in template.get("sample_variants", []):
        if variant.get("id") == variant_id:
            params = variant.get("params")
            if isinstance(params, dict):
                return params
    raise KeyError(f"unknown variant: {template_id}/{variant_id}")
