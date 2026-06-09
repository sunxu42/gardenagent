"""Renderer registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from yard.prompt.context import PromptContext
from yard.prompt.modules import PromptModule

RendererFn = Callable[[PromptModule, PromptContext, "RendererDeps"], str]

_REGISTRY: dict[str, RendererFn] = {}


@dataclass
class RendererDeps:
    prompts_dir: str
    affective_path: str
    agent_mood_path: str
    mood_taxonomy: dict[str, dict[str, Any]]


def register(name: str):
    def deco(fn: RendererFn) -> RendererFn:
        _REGISTRY[name] = fn
        return fn

    return deco


def get_renderer(name: str) -> RendererFn:
    if name not in _REGISTRY:
        raise KeyError(f"unknown renderer: {name}")
    return _REGISTRY[name]


def validate_manifest_renderers(renderer_names: list[str]) -> None:
    for name in renderer_names:
        if name not in _REGISTRY:
            raise KeyError(f"unknown renderer: {name}")


def _ensure_registered() -> None:
    if _REGISTRY:
        return
    from yard.prompt.renderers import affective, mem0, reply_plan  # noqa: F401

_ensure_registered()
