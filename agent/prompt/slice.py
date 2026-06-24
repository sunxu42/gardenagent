"""Load YAML sources and resolve slice paths."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agent.prompt.context import PromptContext

_CTX_REF = re.compile(r"\{ctx\.(\w+)\}")


def interpolate_template(template: str, ctx: PromptContext) -> str:
    def repl(m: re.Match) -> str:
        val = ctx.get(m.group(1))
        return "" if val is None else str(val)

    return _CTX_REF.sub(repl, template)


def resolve_slice(data: Any, path: str) -> Any:
    cur = data
    for part in path.split("."):
        if not part:
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def load_yaml_source(prompts_dir: str | Path, source: str) -> Any:
    path = Path(prompts_dir) / source
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
