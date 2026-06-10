"""主模型调用前：根据用户最新话更新 EmotionService（v2）。"""

from __future__ import annotations

import time
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from yard.emotion.llm.appraisal import EmotionAppraiser, user_text_digest
from yard.emotion.core.service import EmotionService
from yard.observability.logging import LogModule, get_logger
from yard.observability.logging.turn_log import (
    log_emotion_appraisal_done,
    log_emotion_appraisal_start,
)

_log = get_logger(LogModule.EMOTION)


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


def _metrics_from_service(service: EmotionService, digest: str) -> dict | None:
    snap = service.get_appraisal_snapshot(digest)
    return dict(snap) if isinstance(snap, dict) else None


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

    def reset_session_state(self) -> None:
        """清空用户数据后调用，避免 digest 缓存跳过新一轮评估。"""
        self._last_digest = None

    def _run_appraisal(self, request: ModelRequest) -> None:
        user_text = _last_human_text(request.state.get("messages") or [])
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            log_emotion_appraisal_start(cached=True)
            self._service.notify_appraisal_ready(digest)
            metrics = _metrics_from_service(self._service, digest)
            if metrics:
                log_emotion_appraisal_done(duration_sec=0.0, metrics=metrics, cached=True)
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

    async def _run_appraisal_async(self, request: ModelRequest) -> None:
        user_text = _last_human_text(request.state.get("messages") or [])
        if not user_text:
            return
        self._service.begin_turn()
        digest = user_text_digest(user_text)
        if digest == self._last_digest:
            log_emotion_appraisal_start(cached=True)
            self._service.notify_appraisal_ready(digest)
            metrics = _metrics_from_service(self._service, digest)
            if metrics:
                log_emotion_appraisal_done(duration_sec=0.0, metrics=metrics, cached=True)
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

    def wrap_model_call(self, request: ModelRequest, handler):
        try:
            self._run_appraisal(request)
        except Exception as e:
            _log.warning(f"EmotionAppraisalMiddleware sync failed: {e!r}")
        return handler(request)

    async def awrap_model_call(self, request: ModelRequest, handler):
        try:
            await self._run_appraisal_async(request)
        except Exception as e:
            _log.warning(f"EmotionAppraisalMiddleware async failed: {e!r}")
        return await handler(request)
