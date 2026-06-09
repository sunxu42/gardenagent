"""注入 ## User state 与 ## Relationship 段（affective v2）。"""

from __future__ import annotations

from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from langchain_core.messages import SystemMessage
from deepagents.middleware._utils import append_to_system_message

from yard.emotion.core.service import EmotionService
from yard.emotion.rendering.affective_context import render_affective_sections
from yard.prompt.soul import flatten_system_text


class AffectiveContextState(AgentState):
    pass


class AffectiveContextMiddleware(AgentMiddleware[AffectiveContextState, Any]):
    state_schema = AffectiveContextState

    def __init__(
        self,
        service: EmotionService,
        *,
        affective_path: str,
    ) -> None:
        self._service = service
        self._affective_path = affective_path

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        rel = self._service.relationship()
        label = self._service.last_user_emotion_label or "neutral"
        section = render_affective_sections(
            affective_path=self._affective_path,
            user_emotion_label=label,
            trust=rel.trust,
            warmth=rel.warmth,
            interpersonal_cue=self._service.last_interpersonal_cue or "",
        ).strip()
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
