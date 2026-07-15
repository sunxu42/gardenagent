"""LangGraph 对话摘要完成后，将 session buffer flush 到 Mem0。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langgraph.config import get_config
from shared.observability.logging import LogModule, get_logger
from shared.observability.logging.turn_log import log_memory_event

_log = get_logger(LogModule.AGENT)

try:
    from langchain.agents.middleware.types import ExtendedModelResponse
except ImportError:  # pragma: no cover
    ExtendedModelResponse = None  # type: ignore[misc, assignment]


def _thread_id_from_runtime() -> str | None:
    try:
        config = get_config()
        thread_id = config.get("configurable", {}).get("thread_id")
        if isinstance(thread_id, str) and thread_id.strip():
            return thread_id.strip()
    except RuntimeError:
        pass
    return None


class MemoryFlushOnSummarizeMiddleware(AgentMiddleware):
    """在 deepagents SummarizationMiddleware 压缩上下文后触发 Mem0 写入。"""

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    def _should_flush(self) -> bool:
        cfg = getattr(self._agent, "config", None)
        if cfg is None or not getattr(cfg, "memory_enabled", False):
            return False
        return bool(getattr(cfg, "memory_session_flush_on_summarization", True))

    def _summarization_occurred(self, response: ModelResponse) -> bool:
        if ExtendedModelResponse is None or not isinstance(response, ExtendedModelResponse):
            return False
        command = getattr(response, "command", None)
        if command is None:
            return False
        update = getattr(command, "update", None)
        if not isinstance(update, dict):
            return False
        return "_summarization_event" in update

    async def _flush_after_summarization(self) -> None:
        from agent.memory.runtime.flush import flush_agent_session_memory

        thread_id = _thread_id_from_runtime()
        await flush_agent_session_memory(
            self._agent,
            thread_id=thread_id,
            flush_reason="summarization",
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # AgentManager 走异步 agent 路径；同步路径不触发 flush，避免嵌套 event loop。
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        response = await handler(request)
        if self._should_flush() and self._summarization_occurred(response):
            try:
                log_memory_event(
                    "memory flush · summarization triggered",
                    action="flush",
                    flush_reason="summarization",
                )
                await self._flush_after_summarization()
            except Exception as e:
                _log.warning(f"memory summarization flush failed: {e}")
        return response


# Backward-compatible alias
Mem0SummarizationFlushMiddleware = MemoryFlushOnSummarizeMiddleware
