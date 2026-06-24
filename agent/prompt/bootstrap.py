"""Prompt Composer subsystem assembly."""

from __future__ import annotations

from typing import Any

from agent.emotion.core.service import EmotionService
from agent.emotion.rendering.taxonomy import load_taxonomy
from agent.memory.mem0.service import Mem0Service
from agent.middlewares.prompt_composer_middleware import PromptComposerMiddleware
from agent.prompt.context_builder import PromptContextBuilder
from agent.prompt.modules import load_manifest
from agent.prompt.registry import PromptRegistry
from agent.prompt.renderers import RendererDeps


def setup_prompt_composer(
    config: Any,
    *,
    emotion_service: EmotionService | None,
) -> PromptComposerMiddleware | None:
    enabled = bool(getattr(config, "prompt_composer_enabled", False))
    if not enabled:
        return None

    prompts_dir = config.prompts_dir
    affective_path = f"{prompts_dir}/affective.yaml"
    agent_mood_path = f"{prompts_dir}/agent_mood.yaml"
    mood_taxonomy = load_taxonomy(agent_mood_path)
    deps = RendererDeps(
        prompts_dir=prompts_dir,
        affective_path=affective_path,
        agent_mood_path=agent_mood_path,
        mood_taxonomy=mood_taxonomy,
    )
    modules = load_manifest(f"{prompts_dir}/manifest.yaml")
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
    )
