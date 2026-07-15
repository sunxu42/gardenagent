"""Renderer for Danhuang's per-turn reply plan."""

from __future__ import annotations

from typing import Any

import yaml

from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.format_value import format_dialogue_examples
from agent.prompt.compose.module import PromptModule
from agent.prompt.renderers import RendererDeps, register


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
    if plan.presentation_hint == "offer_choice_2plus":
        lines.extend(
            [
                "",
                "### 本回合展示约束（硬性）",
                "你打算提供 ≥2 个可选项并等待用户选择。",
                "步骤：1) 先调用 show_single_select（选好 variant）或其它对应 show_* A2UI tool；"
                "2) 正文最多一句口语邀请点选。",
                "禁止：正文用 1/2/3、「第一第二」、A/B/C 逐条列出所有选项。",
            ]
        )
    elif plan.presentation_hint == "explain_only":
        lines.extend(
            [
                "",
                "### 本回合展示约束",
                "讲解性内容，无表格结构。可用口语说明，不需要调 A2UI tool。",
            ]
        )
    elif plan.presentation_hint == "structured_table":
        lines.extend(
            [
                "",
                "### 本回合展示约束（硬性）",
                "用户需要结构化列举或多行记录（如历年事件、按年清单）。",
                "步骤：1) 先调用 show_data_table(interactive=false)，列好 columns 与 rows；"
                "2) 正文最多一句口语补充。",
                "禁止：在正文用年份逐条罗列或 bullet 列表代替表格。",
            ]
        )
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
