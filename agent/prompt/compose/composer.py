"""PromptComposer: condition filtering, rendering, composition, and budget trimming."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.AGENT)

from agent.prompt.compose.when import evaluate_when
from agent.prompt.compose.context import PromptContext
from agent.prompt.compose.format_value import format_slice_value
from agent.prompt.compose.module import TIER_ORDER, PromptModule
from agent.prompt.compose.yaml_slice import interpolate_template, load_yaml_source, resolve_slice
from agent.prompt.renderers import RendererDeps, get_renderer, validate_manifest_renderers


@dataclass
class ComposeResult:
    text: str
    module_ids: list[str]
    chars: int
    stable_chars: int
    volatile_chars: int


class PromptComposer:
    def __init__(
        self,
        modules: list[PromptModule],
        *,
        deps: RendererDeps,
        budget_enabled: bool = False,
        stable_max_chars: int = 3000,
        volatile_max_chars: int = 1500,
    ) -> None:
        names = [m.renderer for m in modules if m.renderer]
        validate_manifest_renderers(names)
        self._modules = list(modules)
        self._deps = deps
        self._budget_enabled = budget_enabled
        self._stable_max_chars = max(0, int(stable_max_chars))
        self._volatile_max_chars = max(0, int(volatile_max_chars))

    def resolve(self, ctx: PromptContext) -> list[PromptModule]:
        out: list[PromptModule] = []
        for m in self._modules:
            if m.always or evaluate_when(m.when, ctx):
                out.append(m)
        out.sort(
            key=lambda mod: (
                TIER_ORDER.index(mod.tier) if mod.tier in TIER_ORDER else 99,
                mod.priority,
            )
        )
        return out

    def _render_slice_module(self, module: PromptModule, ctx: PromptContext) -> str:
        if not module.source:
            return ""
        data = load_yaml_source(self._deps.prompts_dir, module.source)
        paths = module.slice if isinstance(module.slice, list) else [module.slice]
        blocks: list[str] = []
        for raw_path in paths:
            if not raw_path:
                continue
            path = interpolate_template(str(raw_path), ctx)
            val = resolve_slice(data, path)
            text = format_slice_value(val)
            if text:
                blocks.append(text)
        return "\n\n".join(blocks)

    def _render_module(self, module: PromptModule, ctx: PromptContext) -> str:
        try:
            if module.renderer:
                return get_renderer(module.renderer)(module, ctx, deps=self._deps).strip()
            return self._render_slice_module(module, ctx).strip()
        except Exception as e:
            _log.warning(f"prompt module {module.id!r} render failed: {e!r}")
            return ""

    def _budgeted_pairs(
        self, rendered: list[tuple[PromptModule, str]]
    ) -> list[tuple[PromptModule, str]]:
        if not self._budget_enabled:
            return [(m, t) for m, t in rendered if t]

        stable: list[tuple[PromptModule, str]] = []
        volatile_items: list[tuple[PromptModule, str]] = []
        for mod, text in rendered:
            if not text:
                continue
            if mod.tier == "stable":
                stable.append((mod, text))
            else:
                volatile_items.append((mod, text))

        if stable:
            joined = "\n\n".join(t for _, t in stable)
            if len(joined) > self._stable_max_chars:
                _log.debug(
                    f"prompt budget truncating stable chars {len(joined)} -> {self._stable_max_chars}",
                )
                joined = joined[: self._stable_max_chars].rstrip()
                stable = [(stable[0][0], joined)] if joined else []

        volatile_items.sort(key=lambda x: x[0].priority)
        while volatile_items:
            joined = "\n\n".join(t for _, t in volatile_items)
            if len(joined) <= self._volatile_max_chars:
                break
            dropped = volatile_items.pop()
            _log.debug(f"prompt budget dropped volatile module {dropped[0].id!r}")

        return stable + volatile_items

    def compose_with_meta(self, ctx: PromptContext) -> ComposeResult:
        resolved = self.resolve(ctx)
        rendered = [(m, self._render_module(m, ctx)) for m in resolved]
        kept = self._budgeted_pairs(rendered)
        text = "\n\n".join(t for _, t in kept)
        stable_chars = sum(len(t) for m, t in kept if m.tier == "stable")
        volatile_chars = sum(len(t) for m, t in kept if m.tier != "stable")
        return ComposeResult(
            text=text,
            module_ids=[m.id for m, _ in kept],
            chars=len(text),
            stable_chars=stable_chars,
            volatile_chars=volatile_chars,
        )

    def compose(self, ctx: PromptContext) -> str:
        return self.compose_with_meta(ctx).text

    def compose_meta(self, ctx: PromptContext) -> dict[str, Any]:
        result = self.compose_with_meta(ctx)
        return {
            "module_ids": result.module_ids,
            "chars": result.chars,
            "stable_chars": result.stable_chars,
            "volatile_chars": result.volatile_chars,
            "budget_enabled": self._budget_enabled,
        }


# Backward-compatible alias
PromptRegistry = PromptComposer
