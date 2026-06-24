"""每轮生成前：读 EmotionService 当前 VAD → 投影 → 在 system 末尾注入 ## Mood + few-shot。

应在 Persona / Mem0 等中间件之后注册，使易变 Mood 段位于 system 最后部，利于上下文缓存。
"""

from __future__ import annotations

from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from langchain_core.messages import SystemMessage
from deepagents.middleware._utils import append_to_system_message

from agent.emotion.rendering.taxonomy import render_emotion_sections
from agent.emotion.core.service import EmotionService
from agent.prompt.soul import flatten_system_text


class EmotionMoodState(AgentState):
    pass


class EmotionMoodMiddleware(AgentMiddleware[EmotionMoodState, Any]):
    state_schema = EmotionMoodState

    def __init__(self, service: EmotionService, taxonomy: dict[str, dict]) -> None:
        self._service = service
        self._taxonomy = taxonomy

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        emotion, _scale = self._service.snapshot_for_turn()
        section = render_emotion_sections(self._taxonomy, emotion).strip()
        if not section:
            return request
        base_flat = flatten_system_text(request.system_message)
        new_system_message = append_to_system_message(
            SystemMessage(content=base_flat),
            section,
        )
        return request.override(system_message=new_system_message)

    def wrap_model_call(self, request: ModelRequest, handler):
        return handler(self.modify_request(request))

    async def awrap_model_call(self, request: ModelRequest, handler):
        return await handler(self.modify_request(request))
