"""主模型调用前：根据用户最新话更新 EmotionService（v2）。"""

from __future__ import annotations

from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from loguru import logger

from yard.emotion.llm.appraisal import EmotionAppraiser, user_text_digest
from yard.emotion.core.service import EmotionService


class EmotionAppraisalState(AgentState):
    pass


def _last_human_text(messages: list[Any]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human":
            content = getattr(m, "content", "") or ""
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                return "\n".join(parts).strip()
            return str(content).strip()
    return ""


class EmotionAppraisalMiddleware(AgentMiddleware[EmotionAppraisalState, Any]):
    """须在 EmotionMoodMiddleware 之前注册，以便 snapshot 使用更新后的 VAD。"""

    state_schema = EmotionAppraisalState

    def __init__(
        self,
        service: EmotionService,
        appraiser: EmotionAppraiser,
    ) -> None:
        self._service = service
        self._appraiser = appraiser
        self._last_digest: str | None = None

    def _run_appraisal(self, request: ModelRequest) -> None:
        user_text = _last_human_text(request.state.get("messages") or [])
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            self._service.notify_appraisal_ready(digest)
            return
        appraisal = self._appraiser.appraise_v2(user_text)
        if appraisal is None:
            return
        vad = self._service.synthesize_and_apply_v2(appraisal)
        if vad is not None:
            synthesis = self._service.last_synthesis()
            if synthesis is not None:
                self._last_digest = digest
                self._service.record_appraisal_snapshot(digest, appraisal, synthesis)

    async def _run_appraisal_async(self, request: ModelRequest) -> None:
        user_text = _last_human_text(request.state.get("messages") or [])
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            self._service.notify_appraisal_ready(digest)
            return
        appraisal = await self._appraiser.appraise_v2_async(user_text)
        if appraisal is None:
            return
        vad = self._service.synthesize_and_apply_v2(appraisal)
        if vad is not None:
            synthesis = self._service.last_synthesis()
            if synthesis is not None:
                self._last_digest = digest
                self._service.record_appraisal_snapshot(digest, appraisal, synthesis)

    def wrap_model_call(self, request: ModelRequest, handler):
        try:
            self._run_appraisal(request)
        except Exception as e:
            logger.warning("EmotionAppraisalMiddleware sync failed: {!r}", e)
        return handler(request)

    async def awrap_model_call(self, request: ModelRequest, handler):
        try:
            await self._run_appraisal_async(request)
        except Exception as e:
            logger.warning("EmotionAppraisalMiddleware async failed: {!r}", e)
        return await handler(request)
