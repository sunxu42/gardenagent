from __future__ import annotations

from agent.prompt.context import PromptContext
from agent.prompt.modules import PromptModule
from agent.prompt.renderers import RendererDeps, register


@register("mem0.bullets")
def render_mem0_bullets(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    bullets = (ctx.memory_bullets or "").strip()
    if not bullets:
        return ""
    return "## Long-term memory\n\n" + bullets
