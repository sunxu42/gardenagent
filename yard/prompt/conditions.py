"""manifest `when` 条件表达式求值（安全子集）。"""

from __future__ import annotations

import re

from yard.prompt.context import PromptContext

_CMP_RE = re.compile(
    r"^\s*ctx\.(\w+)\s*(>=|<=|==|!=)\s*(.+?)\s*$"
)
_BARE_RE = re.compile(r"^\s*ctx\.(\w+)\s*$")


def _parse_value(raw: str):
    s = raw.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _compare(field_val, op: str, target) -> bool:
    if op == "==":
        return field_val == target
    if op == "!=":
        return field_val != target
    if op == ">=":
        return float(field_val) >= float(target)
    if op == "<=":
        return float(field_val) <= float(target)
    return False


def _truthy(field_val) -> bool:
    if isinstance(field_val, bool):
        return field_val
    if isinstance(field_val, (int, float)):
        return field_val != 0
    if isinstance(field_val, str):
        return bool(field_val.strip())
    return field_val is not None


def _eval_atom(expr: str, ctx: PromptContext) -> bool:
    expr = expr.strip()
    m = _CMP_RE.match(expr)
    if m:
        name, op, raw = m.group(1), m.group(2), m.group(3)
        return _compare(ctx.get(name), op, _parse_value(raw))
    m = _BARE_RE.match(expr)
    if m:
        return _truthy(ctx.get(m.group(1)))
    return False


def _eval_or_group(group: str, ctx: PromptContext) -> bool:
    parts = [p.strip() for p in group.split(" or ") if p.strip()]
    return any(_eval_atom(p, ctx) for p in parts)


def evaluate_when(expr: str | None, ctx: PromptContext) -> bool:
    if expr is None:
        return True
    s = str(expr).strip()
    if not s or s.lower() in ("always", "true"):
        return True
    if s.lower() == "false":
        return False
    and_groups = [g.strip() for g in s.split(" and ") if g.strip()]
    return all(_eval_or_group(g, ctx) for g in and_groups)
