from __future__ import annotations

from yard.prompt.context import PromptContext
from yard.prompt.modules import PromptModule
from yard.prompt.renderers import RendererDeps, register


@register("mem0.bullets")
def render_mem0_bullets(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    bullets = (ctx.memory_bullets or "").strip()
    if not bullets:
        return ""
    return "## 长期记忆\n\n" + bullets
