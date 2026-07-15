"""Declarative system-prompt composition pipeline."""

from agent.prompt.compose.build_context import PromptContextBuilder
from agent.prompt.compose.composer import ComposeResult, PromptComposer
from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.module import PromptModule, load_manifest

__all__ = [
    "ComposeResult",
    "PromptComposer",
    "PromptContext",
    "PromptContextBuilder",
    "PromptModule",
    "load_manifest",
]
