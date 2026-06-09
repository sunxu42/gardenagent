"""Prompt Composer 子系统装配。"""

from __future__ import annotations

from typing import Any

from yard.emotion.core.service import EmotionService
from yard.emotion.rendering.taxonomy import load_taxonomy
from yard.memory.mem0.service import Mem0Service
from yard.middlewares.prompt_composer_middleware import PromptComposerMiddleware
from yard.prompt.context_builder import PromptContextBuilder
from yard.prompt.modules import load_manifest
from yard.prompt.registry import PromptRegistry
from yard.prompt.renderers import RendererDeps


def setup_prompt_composer(
    config: Any,
    *,
    emotion_service: EmotionService | None,
) -> PromptComposerMiddleware | None:
    enabled = bool(getattr(config, "prompt_composer_enabled", False))
    shadow = bool(getattr(config, "prompt_composer_shadow", False))
    if not enabled and not shadow:
        return None

    prompts_dir = config.prompts_dir
    mood_taxonomy = load_taxonomy(f"{prompts_dir}/moods/levels.yaml")
    deps = RendererDeps(
        prompts_dir=prompts_dir,
        mood_taxonomy=mood_taxonomy,
        user_states_path=f"{prompts_dir}/user_states.yaml",
        relationship_stages_path=f"{prompts_dir}/relationship_stages.yaml",
    )
    use_tiered = bool(getattr(config, "prompt_composer_tiered", False))
    manifest_file = "manifest.tiered.yaml" if use_tiered else "manifest.yaml"
    modules = load_manifest(f"{prompts_dir}/{manifest_file}")
    registry = PromptRegistry(
        modules,
        deps=deps,
        budget_enabled=bool(getattr(config, "prompt_budget_enabled", False)),
        stable_max_chars=int(getattr(config, "prompt_stable_max_chars", 3000)),
        volatile_max_chars=int(getattr(config, "prompt_volatile_max_chars", 1500)),
    )

    def format_memories(memories: list) -> str:
        return Mem0Service.format_bullets(
            memories,
            max_chars=config.mem0_inject_max_chars,
        )

    builder = PromptContextBuilder(
        config=config,
        emotion_service=emotion_service,
        mem0_format_fn=format_memories,
    )
    return PromptComposerMiddleware(
        registry,
        builder,
        prompts_dir=prompts_dir,
        shadow=shadow and not enabled,
    )
