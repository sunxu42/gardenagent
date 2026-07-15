"""Agent mood taxonomy sections for the system prompt."""

from __future__ import annotations

from agent.emotion.rendering.taxonomy import render_emotion_sections
from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.module import PromptModule
from agent.prompt.renderers import RendererDeps, register


@register("emotion.mood")
def render_emotion_mood(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    return render_emotion_sections(deps.mood_taxonomy, ctx.agent_emotion).strip()
