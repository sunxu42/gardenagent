"""单点 system prompt 拼接（Prompt Composer）。"""

from __future__ import annotations

from typing import Any

from deepagents.middleware._utils import append_to_system_message
from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from langchain_core.messages import SystemMessage
from loguru import logger

from yard.prompt.context_builder import PromptContextBuilder
from yard.prompt.registry import PromptRegistry
from yard.middlewares.persona_prompt_middleware import _SoulYamlComposer, render_system_prompt_generic
from yard.prompt.soul import flatten_system_text


class PromptComposerState(AgentState):
    pass


def _fallback_core_text(prompts_dir: str) -> str:
    try:
        composer = _SoulYamlComposer(prompts_dir)
        data = composer.load_soul()
        blocks = []
        system = data.get("system")
        if isinstance(system, dict):
            ident = system.get("identity")
            safety = (system.get("rules") or {}).get("safety")
            if isinstance(ident, str) and ident.strip():
                blocks.append(ident.strip())
            if isinstance(safety, list):
                blocks.extend(str(x) for x in safety if str(x).strip())
        if blocks:
            return "\n\n".join(blocks)
        return render_system_prompt_generic(data)[:800]
    except Exception as e:
        logger.warning("prompt composer fallback failed: {!r}", e)
        return "你是语音助手。请安全、清晰地回答用户。"


class PromptComposerMiddleware(AgentMiddleware[PromptComposerState, Any]):
    state_schema = PromptComposerState

    def __init__(
        self,
        registry: PromptRegistry,
        builder: PromptContextBuilder,
        *,
        prompts_dir: str,
        shadow: bool = False,
    ) -> None:
        self._registry = registry
        self._builder = builder
        self._prompts_dir = prompts_dir
        self._shadow = shadow

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        ctx = self._builder.build(request)
        result = self._registry.compose_with_meta(ctx)
        text = result.text.strip() or _fallback_core_text(self._prompts_dir)

        logger.debug(
            "prompt.compose modules={} chars={} stable={} volatile={} shadow={}",
            result.module_ids,
            result.chars,
            result.stable_chars,
            result.volatile_chars,
            self._shadow,
        )

        if self._shadow:
            return request

        base_flat = flatten_system_text(request.system_message)
        if base_flat:
            combined = append_to_system_message(SystemMessage(content=base_flat), text)
            return request.override(system_message=combined)
        return request.override(system_message=SystemMessage(content=text))

    def wrap_model_call(self, request: ModelRequest, handler):
        return handler(self.modify_request(request))

    async def awrap_model_call(self, request: ModelRequest, handler):
        return await handler(self.modify_request(request))
