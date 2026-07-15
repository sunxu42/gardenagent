"""Long-term memory section for the system prompt."""

from __future__ import annotations

from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.module import PromptModule
from agent.prompt.renderers import RendererDeps, register


@register("memory.bullets")
def render_memory_bullets(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    bullets = (ctx.memory_bullets or "").strip()
    if not bullets:
        return ""
    return "## Long-term memory\n\n" + bullets


# Keep old registration name working for older manifests.
register("mem0.bullets")(render_memory_bullets)
