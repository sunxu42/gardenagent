from __future__ import annotations

from yard.emotion.rendering.affective_context import (
    render_affective_sections,
    render_relationship_section,
    render_user_state_section,
)
from yard.prompt.context import PromptContext
from yard.prompt.modules import PromptModule
from yard.prompt.renderers import RendererDeps, register


def _label(ctx: PromptContext) -> str:
    return ctx.user_emotion_label or "neutral"


@register("affective.full")
def render_affective_full(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    if not ctx.affective_v2_enabled:
        return ""
    return render_affective_sections(
        user_states_path=deps.user_states_path,
        relationship_stages_path=deps.relationship_stages_path,
        user_emotion_label=_label(ctx),
        trust=ctx.trust,
        warmth=ctx.warmth,
        interpersonal_cue=ctx.interpersonal_cue,
        response_policy=ctx.response_policy,
    )


@register("affective.user_state")
def render_affective_user_state(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    if not ctx.affective_v2_enabled:
        return ""
    return render_user_state_section(
        user_states_path=deps.user_states_path,
        user_emotion_label=_label(ctx),
    )


@register("affective.relationship")
def render_affective_relationship(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    if not ctx.affective_v2_enabled:
        return ""
    return render_relationship_section(
        relationship_stages_path=deps.relationship_stages_path,
        trust=ctx.trust,
        warmth=ctx.warmth,
        interpersonal_cue=ctx.interpersonal_cue,
        response_policy=ctx.response_policy,
    )
