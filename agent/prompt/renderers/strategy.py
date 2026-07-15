"""Renderer for per-turn strategy tags."""

from __future__ import annotations

from agent.emotion.synthesis.strategy_tags import strategy_tags_summary
from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.module import PromptModule
from agent.prompt.renderers import RendererDeps, register


@register("strategy")
def render_strategy(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    tags = ctx.strategy_tags
    if tags is None:
        return ""
    summary = strategy_tags_summary(tags)
    lines = [
        "## Strategy",
        f"Tags: mode={tags.mode}, voice={tags.voice_style}, length={tags.length}, tts={tags.tts_profile}",
    ]
    if summary:
        lines.append(f"Summary: {summary}")
    if tags.llm_guideline:
        lines.append(f"Hard constraints: {tags.llm_guideline}")
    return "\n".join(lines).strip()
