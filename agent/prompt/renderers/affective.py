from __future__ import annotations

from agent.emotion.rendering.affective_context import (
    render_relationship_section,
    render_user_state_section,
)
from agent.prompt.context import PromptContext
from agent.prompt.modules import PromptModule
from agent.prompt.renderers import RendererDeps, register


def _label(ctx: PromptContext) -> str:
    return ctx.user_emotion_label or "neutral"


@register("affective.user_state")
def render_affective_user_state(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    if not ctx.affective_v2_enabled:
        return ""
    return render_user_state_section(
        affective_path=deps.affective_path,
        user_emotion_label=_label(ctx),
    )


@register("affective.relationship")
def render_affective_relationship(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    if not ctx.affective_v2_enabled:
        return ""
    return render_relationship_section(
        affective_path=deps.affective_path,
        trust=ctx.trust,
        warmth=ctx.warmth,
        interpersonal_cue=ctx.interpersonal_cue,
    )
