from __future__ import annotations

from yard.emotion.rendering.taxonomy import DEFAULT_EMOTION, render_emotion_sections
from yard.prompt.context import PromptContext
from yard.prompt.formatting import format_dialogue_examples
from yard.prompt.modules import PromptModule
from yard.prompt.renderers import RendererDeps, register
from yard.prompt.slice import load_yaml_source, resolve_slice


def _emotion_entry(deps: RendererDeps, emotion: str) -> dict:
    return deps.mood_taxonomy.get(emotion) or deps.mood_taxonomy.get(DEFAULT_EMOTION) or {}


@register("mood.bundle")
def render_mood_bundle(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    emotion = (ctx.agent_emotion or "neutral").strip() or "neutral"
    return render_emotion_sections(deps.mood_taxonomy, emotion)


@register("mood.guidance")
def render_mood_guidance(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    emotion = (ctx.agent_emotion or "neutral").strip() or "neutral"
    entry = _emotion_entry(deps, emotion)
    label = str(entry.get("label_zh") or emotion).strip()
    guidance = str(entry.get("guidance") or "").strip()
    lines = [f"Current mood: {label} ({emotion})", ""]
    if guidance:
        lines.append(guidance)
    return "## Mood\n" + "\n".join(lines).strip()


@register("mood.strategy")
def render_mood_strategy(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    emotion = (ctx.agent_emotion or "neutral").strip() or "neutral"
    mode = (ctx.empathy_mode or "neutral").strip() or "neutral"
    try:
        data = load_yaml_source(deps.prompts_dir, "moods/strategies.yaml")
    except OSError:
        return ""
    tactics = resolve_slice(data, f"{emotion}.{mode}.tactics")
    if not isinstance(tactics, str) or not tactics.strip():
        tactics = resolve_slice(data, f"{emotion}.neutral.tactics")
    if not isinstance(tactics, str) or not tactics.strip():
        return ""
    return "## Mood strategy\n" + tactics.strip()


@register("mood.few_shot")
def render_mood_few_shot(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    emotion = (ctx.agent_emotion or "neutral").strip() or "neutral"
    entry = _emotion_entry(deps, emotion)
    examples = entry.get("speech_examples")
    if not isinstance(examples, list) or not examples:
        return ""
    body = format_dialogue_examples(examples, limit=2)
    if not body:
        return ""
    header = (
        "## Mood speech examples (few-shot)\n"
        "Match the tone and pacing of these examples. "
        "Reply in Simplified Chinese unless the user clearly asks for English.\n"
    )
    return header + "\n" + body
