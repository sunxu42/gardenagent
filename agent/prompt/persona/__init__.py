"""Persona identity / voice / baseline loaded from soul.yaml."""

from agent.prompt.persona.soul_profile import (
    SoulProfileLoader,
    render_system_prompt_generic,
    resolve_soul_profile,
)

__all__ = ["SoulProfileLoader", "render_system_prompt_generic", "resolve_soul_profile"]
