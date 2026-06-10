"""Renderer for Danhuang's per-turn reply plan."""

from __future__ import annotations

from typing import Any

import yaml

from yard.prompt.context import PromptContext
from yard.prompt.formatting import format_dialogue_examples
from yard.prompt.modules import PromptModule
from yard.prompt.renderers import RendererDeps, register


_MAX_REPLY_EXAMPLES = 2


@register("reply_plan")
def render_reply_plan(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    """Render the deterministic reply plan for the current turn."""
    plan = ctx.reply_plan
    if plan is None:
        return ""

    lines = []
    if ctx.strategy_tags is not None and ctx.strategy_tags.llm_guideline:
        lines.append(f"Hard constraints: {ctx.strategy_tags.llm_guideline}")
    lines.extend([
        "## Reply plan",
        f"Turn goal: {plan.intent}",
        f"Opening move: {plan.opening_move}",
        "Reply structure:",
    ])
    lines.extend(f"- {item}" for item in plan.structure)
    lines.append("Voice and tone:")
    lines.extend(f"- {item}" for item in plan.voice)
    lines.append("Avoid:")
    lines.extend(f"- {item}" for item in plan.boundaries)
    if plan.few_shot_tags:
        lines.append("Few-shot tags: " + ", ".join(plan.few_shot_tags))
    examples = _select_reply_examples(deps.affective_path, plan.few_shot_tags)
    if examples:
        lines.append("")
        lines.append("## Reply examples")
        lines.append("Use these examples for tone and pacing; do not copy them verbatim.")
        lines.append(format_dialogue_examples(examples))
    lines.append(f"Directiveness: {plan.directiveness:.2f}")
    return "\n".join(lines).strip()


def _select_reply_examples(affective_path: str, tags: list[str]) -> list[dict[str, Any]]:
    tag_set = {tag.strip() for tag in tags if tag.strip()}
    if not tag_set:
        return []

    try:
        with open(affective_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except OSError:
        return []

    raw_examples = data.get("reply_examples")
    if not isinstance(raw_examples, list):
        return []

    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(raw_examples):
        if not isinstance(item, dict):
            continue
        item_tags = item.get("tags")
        if not isinstance(item_tags, list):
            continue
        example_tags = {str(tag).strip() for tag in item_tags if str(tag).strip()}
        score = len(tag_set & example_tags)
        if score <= 0:
            continue
        scored.append((score, -index, item))

    scored.sort(reverse=True)
    return [item for _, _, item in scored[:_MAX_REPLY_EXAMPLES]]
