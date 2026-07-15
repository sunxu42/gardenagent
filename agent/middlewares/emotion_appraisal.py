"""用户每轮输入开始时：根据最新话更新 EmotionService（v2）。"""

from __future__ import annotations

import time
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState

from agent.emotion.core.service import EmotionService
from agent.emotion.llm.appraisal import EmotionAppraiser, user_text_digest
from agent.prompt.chat_text import last_human_text
from shared.observability.logging import LogModule, get_logger
from shared.observability.logging.turn_log import (
    log_emotion_appraisal_done,
    log_emotion_appraisal_start,
)

_log = get_logger(LogModule.EMOTION)


class EmotionAppraisalState(AgentState):
    pass


def _metrics_from_service(service: EmotionService, digest: str) -> dict | None:
    snap = service.get_appraisal_snapshot(digest)
    return dict(snap) if isinstance(snap, dict) else None


class EmotionAppraisalMiddleware(AgentMiddleware[EmotionAppraisalState, Any]):
    """在 SystemPromptMiddleware 之前注册，以便 snapshot 使用更新后的 VAD。"""

    state_schema = EmotionAppraisalState

    def __init__(
        self,
        service: EmotionService,
        appraiser: EmotionAppraiser,
    ) -> None:
        self._service = service
        self._appraiser = appraiser
        self._last_digest: str | None = None

    def reset_session_state(self) -> None:
        """清空用户数据后调用，避免 digest 缓存跳过新一轮评估。"""
        self._last_digest = None

    def _appraise_from_messages(self, messages: list[Any]) -> None:
        user_text = last_human_text(messages)
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            self._service.notify_appraisal_ready(digest)
            return
        log_emotion_appraisal_start(cached=False)
        t0 = time.perf_counter()
        appraisal = self._appraiser.appraise_v2(user_text)
        if appraisal is None:
            _log.warning("emotion appraisal · failed (no result)")
            return
        vad = self._service.synthesize_and_apply_v2(appraisal)
        if vad is None:
            _log.warning("emotion appraisal · synthesis failed")
            return
        synthesis = self._service.last_synthesis()
        if synthesis is None:
            return
        self._last_digest = digest
        self._service.record_appraisal_snapshot(digest, appraisal, synthesis)
        metrics = _metrics_from_service(self._service, digest)
        if metrics:
            log_emotion_appraisal_done(
                duration_sec=time.perf_counter() - t0,
                metrics=metrics,
                cached=False,
            )

    async def _appraise_from_messages_async(self, messages: list[Any]) -> None:
        user_text = last_human_text(messages)
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            self._service.notify_appraisal_ready(digest)
            return
        log_emotion_appraisal_start(cached=False)
        t0 = time.perf_counter()
        appraisal = await self._appraiser.appraise_v2_async(user_text)
        if appraisal is None:
            _log.warning("emotion appraisal · failed (no result)")
            return
        vad = self._service.synthesize_and_apply_v2(appraisal)
        if vad is None:
            _log.warning("emotion appraisal · synthesis failed")
            return
        synthesis = self._service.last_synthesis()
        if synthesis is None:
            return
        self._last_digest = digest
        self._service.record_appraisal_snapshot(digest, appraisal, synthesis)
        metrics = _metrics_from_service(self._service, digest)
        if metrics:
            log_emotion_appraisal_done(
                duration_sec=time.perf_counter() - t0,
                metrics=metrics,
                cached=False,
            )

    def before_agent(self, state: EmotionAppraisalState, runtime) -> None:
        try:
            self._appraise_from_messages(state.get("messages") or [])
        except Exception as e:
            _log.warning(f"EmotionAppraisalMiddleware before_agent failed: {e!r}")

    async def abefore_agent(self, state: EmotionAppraisalState, runtime) -> None:
        try:
            await self._appraise_from_messages_async(state.get("messages") or [])
        except Exception as e:
            _log.warning(f"EmotionAppraisalMiddleware abefore_agent failed: {e!r}")
