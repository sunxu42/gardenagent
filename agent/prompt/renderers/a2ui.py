"""Renderer for A2UI tool selection rules."""

from __future__ import annotations

from agent.a2ui.prompt import render_a2ui_system_prompt
from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.module import PromptModule
from agent.prompt.renderers import RendererDeps, register


@register("a2ui.tools")
def render_a2ui_tools(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    return render_a2ui_system_prompt()
