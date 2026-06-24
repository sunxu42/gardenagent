"""Prompt Composer: declarative module registration and system prompt composition."""

from agent.prompt.context import PromptContext
from agent.prompt.registry import PromptRegistry

__all__ = ["PromptContext", "PromptRegistry"]
