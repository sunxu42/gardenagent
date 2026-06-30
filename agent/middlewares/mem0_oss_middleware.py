"""
Mem0OssMiddleware: Mem0 OSS 长期记忆（FAISS 本地）。

- before_agent: 检索注入 + 显式关键词 remember（不每轮 after_model add）
- modify_request: 注入 Mem0 检索结果（不读 MEMORY.md）
"""

from __future__ import annotations

from typing import Any, Dict, List, NotRequired

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest
from deepagents.middleware._utils import append_to_system_message
from shared.observability.logging import LogModule, get_logger
from shared.observability.logging.turn_log import log_memory_event

_log = get_logger(LogModule.AGENT)
from typing_extensions import TypedDict

from langgraph.config import get_config

from agent.configs.settings import Config
from agent.memory.core.triggers import ExplicitTriggerConfig, detect_explicit_remember
from agent.memory.mem0.service import Mem0Service
from agent.memory.core.buffer import SessionBuffer


class Mem0OssState(AgentState):
    mem0_memories: NotRequired[List[Dict[str, Any]]]
    mem0_explicit_added: NotRequired[bool]


class Mem0OssStateUpdate(TypedDict):
    mem0_memories: List[Dict[str, Any]]
    mem0_explicit_added: bool


def _last_human_text(messages: list[Any]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human":
            content = getattr(m, "content", "") or ""
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                return "\n".join(parts).strip()
            return str(content).strip()
    return ""


def _thread_id_from_state(state: Mem0OssState) -> str:
    return (
        state.get("thread_id")
        or state.get("session_id")
        or "default"
    )


def _user_id_from_runtime() -> str | None:
    try:
        config = get_config()
        tid = config.get("configurable", {}).get("thread_id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
    except RuntimeError:
        pass
    return None


def _user_id_from_state(state: Mem0OssState) -> str:
    tid = _thread_id_from_state(state)
    if tid and tid != "default":
        return tid
    runtime = _user_id_from_runtime()
    if runtime:
        return runtime
    return "default"


class Mem0OssMiddleware(AgentMiddleware[Mem0OssState, Any]):
    state_schema = Mem0OssState

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

    def _resolve_user_id(self, state: Mem0OssState) -> str:
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

    def before_agent(self, state: Mem0OssState, runtime) -> Mem0OssStateUpdate | None:
        messages = state.get("messages") or []
        thread_id = _thread_id_from_state(state)

        if self.session_buffer is not None:
            self.session_buffer.append_from_state(thread_id, messages)

        uid = self._resolve_user_id(state)
        last_user = _last_human_text(messages)
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

        return Mem0OssStateUpdate(
            mem0_memories=memories,
            mem0_explicit_added=explicit_added,
        )

    async def abefore_agent(self, state: Mem0OssState, runtime) -> Mem0OssStateUpdate | None:
        messages = state.get("messages") or []
        thread_id = _thread_id_from_state(state)

        if self.session_buffer is not None:
            self.session_buffer.append_from_state(thread_id, messages)

        uid = self._resolve_user_id(state)
        last_user = _last_human_text(messages)
        explicit_added = bool(state.get("mem0_explicit_added"))

        if self.config.memory_explicit_keyword_enabled and last_user and not explicit_added:
            match = detect_explicit_remember(last_user, self._explicit_config)
            if match:
                try:
                    if self._debug_log_enabled:
                        _log.info(
                            f"[mem0:add:explicit_keyword] embedding_input(user): {self._truncate(match.fact_text)}",
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

        return Mem0OssStateUpdate(
            mem0_memories=memories,
            mem0_explicit_added=explicit_added,
        )

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        if getattr(self.config, "prompt_composer_enabled", False):
            return request
        memories = request.state.get("mem0_memories") or []
        bullets = Mem0Service.format_bullets(
            memories,
            max_chars=self.config.mem0_inject_max_chars,
        )
        if not bullets:
            return request

        extra = "## 长期记忆\n\n" + bullets
        new_system_message = append_to_system_message(request.system_message, extra)
        return request.override(system_message=new_system_message)

    def wrap_model_call(self, request: ModelRequest, handler):
        return handler(self.modify_request(request))

    async def awrap_model_call(self, request: ModelRequest, handler):
        return await handler(self.modify_request(request))
