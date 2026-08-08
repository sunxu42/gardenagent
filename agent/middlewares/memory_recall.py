"""检索长期记忆并处理显式 remember；不写入 system prompt（由 SystemPrompt 注入）。"""

from __future__ import annotations

from typing import Any, Dict, List, NotRequired

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langgraph.config import get_config
from typing_extensions import TypedDict

from shared.config.agent import Config
from agent.memory.core.buffer import SessionBuffer
from agent.memory.core.triggers import ExplicitTriggerConfig, detect_explicit_remember
from agent.memory.mem0.service import Mem0Service
from agent.prompt.chat_text import last_human_text
from shared.observability.logging import LogModule, get_logger
from shared.observability.logging.turn_log import log_memory_event

_log = get_logger(LogModule.AGENT)


class MemoryRecallState(AgentState):
    mem0_memories: NotRequired[List[Dict[str, Any]]]
    mem0_explicit_added: NotRequired[bool]


class MemoryRecallStateUpdate(TypedDict):
    mem0_memories: List[Dict[str, Any]]
    mem0_explicit_added: bool


def _thread_id_from_state(state: MemoryRecallState) -> str:
    return state.get("thread_id") or state.get("session_id") or "default"


def _user_id_from_runtime() -> str | None:
    try:
        config = get_config()
        tid = config.get("configurable", {}).get("thread_id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
    except RuntimeError:
        pass
    return None


def _user_id_from_state(state: MemoryRecallState) -> str:
    tid = _thread_id_from_state(state)
    if tid and tid != "default":
        return tid
    runtime = _user_id_from_runtime()
    if runtime:
        return runtime
    return "default"


class MemoryRecallMiddleware(AgentMiddleware[MemoryRecallState, Any]):
    """Search Mem0 + explicit keyword remember; stores hits on agent state."""

    state_schema = MemoryRecallState

    def __init__(
        self,
        service: Mem0Service,
        config: Config,
        *,
        session_buffer: SessionBuffer | None = None,
        default_user_id: str | None = None,
    ) -> None:
        self.service = service
        self.config = config
        self.session_buffer = session_buffer
        self.default_user_id = default_user_id or service.default_user_id
        self._explicit_config = ExplicitTriggerConfig(
            enabled=config.memory_explicit_keyword_enabled,
            keywords_zh=config.memory_explicit_keywords_zh,
            keywords_en=config.memory_explicit_keywords_en,
            negative_patterns=config.memory_explicit_negative_patterns,
            weak_zh_enabled=config.memory_explicit_weak_zh_enabled,
            weak_en_enabled=config.memory_explicit_weak_en_enabled,
        )
        self._debug_log_enabled = bool(getattr(config, "memory_debug_log_enabled", False))
        self._debug_log_max_chars = int(getattr(config, "memory_debug_log_max_chars", 500) or 500)

    def _truncate(self, text: str) -> str:
        t = (text or "").strip()
        n = self._debug_log_max_chars
        if n <= 0:
            return ""
        return t if len(t) <= n else (t[: n - 1] + "…")

    def _resolve_user_id(self, state: MemoryRecallState) -> str:
        uid = _user_id_from_state(state)
        if isinstance(uid, str) and uid.strip() and uid.strip() != "default":
            return uid.strip()
        fallback = self.default_user_id if isinstance(self.default_user_id, str) else ""
        fallback = fallback.strip()
        return fallback or "default"

    def _maybe_explicit_add(
        self, user_text: str, *, user_id: str, already_added: bool
    ) -> bool:
        if already_added or not self.config.memory_explicit_keyword_enabled:
            return already_added
        match = detect_explicit_remember(user_text, self._explicit_config)
        if not match:
            return already_added
        try:
            if self._debug_log_enabled:
                _log.info(
                    f"[mem0:add:explicit_keyword] embedding_input(user): {self._truncate(match.fact_text)}",
                )
            self.service.add(
                [{"role": "user", "content": match.fact_text}],
                user_id=user_id,
                metadata={
                    "source": "explicit_keyword",
                    "pinned": True,
                    "category": "preference",
                },
                infer=True,
            )
            log_memory_event(
                f"memory write · explicit keyword ({len(match.fact_text)} chars)",
                action="explicit_add",
                source="explicit_keyword",
                char_count=len(match.fact_text),
            )
            return True
        except Exception as e:
            _log.warning(f"Mem0 explicit_keyword add failed: {e!r}")
            return already_added

    def before_agent(self, state: MemoryRecallState, runtime) -> MemoryRecallStateUpdate | None:
        messages = state.get("messages") or []
        thread_id = _thread_id_from_state(state)

        if self.session_buffer is not None:
            self.session_buffer.append_from_state(thread_id, messages)

        uid = self._resolve_user_id(state)
        last_user = last_human_text(messages)
        explicit_added = bool(state.get("mem0_explicit_added"))
        explicit_added = self._maybe_explicit_add(
            last_user, user_id=uid, already_added=explicit_added
        )

        memories: list[dict[str, Any]] = []
        if last_user:
            try:
                memories = self.service.search(
                    last_user,
                    user_id=uid,
                    limit=self.config.mem0_top_k,
                )
            except Exception as e:
                _log.warning(f"Mem0 search failed: {e!r}")
        if last_user:
            log_memory_event(
                f"memory search · {len(memories)} hits",
                action="search",
                hit_count=len(memories),
            )

        return MemoryRecallStateUpdate(
            mem0_memories=memories,
            mem0_explicit_added=explicit_added,
        )

    async def abefore_agent(
        self, state: MemoryRecallState, runtime
    ) -> MemoryRecallStateUpdate | None:
        messages = state.get("messages") or []
        thread_id = _thread_id_from_state(state)

        if self.session_buffer is not None:
            self.session_buffer.append_from_state(thread_id, messages)

        uid = self._resolve_user_id(state)
        last_user = last_human_text(messages)
        explicit_added = bool(state.get("mem0_explicit_added"))

        if self.config.memory_explicit_keyword_enabled and last_user and not explicit_added:
            match = detect_explicit_remember(last_user, self._explicit_config)
            if match:
                try:
                    if self._debug_log_enabled:
                        _log.info(
                            f"[mem0:add:explicit_keyword] embedding_input(user): "
                            f"{self._truncate(match.fact_text)}",
                        )
                    await self.service.aadd(
                        [{"role": "user", "content": match.fact_text}],
                        user_id=uid,
                        metadata={
                            "source": "explicit_keyword",
                            "pinned": True,
                            "category": "preference",
                        },
                        infer=True,
                    )
                    explicit_added = True
                    log_memory_event(
                        f"memory write · explicit keyword ({len(match.fact_text)} chars)",
                        action="explicit_add",
                        source="explicit_keyword",
                        char_count=len(match.fact_text),
                    )
                except Exception as e:
                    _log.warning(f"Mem0 explicit_keyword add failed: {e!r}")

        memories: list[dict[str, Any]] = []
        if last_user:
            try:
                memories = await self.service.asearch(
                    last_user,
                    user_id=uid,
                    limit=self.config.mem0_top_k,
                )
            except Exception as e:
                _log.warning(f"Mem0 search failed: {e!r}")
            log_memory_event(
                f"memory search · {len(memories)} hits",
                action="search",
                hit_count=len(memories),
            )

        return MemoryRecallStateUpdate(
            mem0_memories=memories,
            mem0_explicit_added=explicit_added,
        )


# Backward-compatible aliases
Mem0OssMiddleware = MemoryRecallMiddleware
Mem0OssState = MemoryRecallState
