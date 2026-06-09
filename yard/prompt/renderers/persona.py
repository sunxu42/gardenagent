from __future__ import annotations

from yard.middlewares.persona_prompt_middleware import _SoulYamlComposer, render_system_prompt_generic
from yard.prompt.context import PromptContext
from yard.prompt.formatting import format_dialogue_examples
from yard.prompt.modules import PromptModule
from yard.prompt.renderers import RendererDeps, register


@register("persona.generic")
def render_persona_generic(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    composer = _SoulYamlComposer(deps.prompts_dir)
    return render_system_prompt_generic(composer.load_soul())


@register("persona.examples")
def render_persona_examples(module: PromptModule, ctx: PromptContext, *, deps: RendererDeps) -> str:
    composer = _SoulYamlComposer(deps.prompts_dir)
    data = composer.load_soul()
    examples = data.get("speech_examples")
    if not isinstance(examples, list) or not examples:
        return ""
    body = format_dialogue_examples(examples)
    if not body:
        return ""
    return "## Persona speech examples\n" + body
