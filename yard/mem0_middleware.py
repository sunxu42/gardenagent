"""
Mem0Middleware: 将 Mem0 长期记忆接入 DeepAgents。

功能概述：
- 在每次对话前，从 Mem0 检索与当前用户/线程相关的记忆，追加到 system 或 context 中；
- 在模型回复后，把本轮对话摘要写回 Mem0，形成长期记忆。

依赖：
- pip install mem0ai
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from deepagents.middleware._utils import append_to_system_message
from typing_extensions import NotRequired, TypedDict


class Mem0State(AgentState):
    """State schema for Mem0Middleware."""

    mem0_memories: NotRequired[List[Dict[str, Any]]]


class Mem0StateUpdate(TypedDict):
    """State update for Mem0Middleware."""

    mem0_memories: List[Dict[str, Any]]

try:
    from mem0 import MemoryClient
except ImportError:  # pragma: no cover - 运行时缺依赖时直接提示
    MemoryClient = None  # type: ignore[assignment]


class Mem0Middleware(AgentMiddleware[Mem0State, Any]):

    state_schema = Mem0State

    def __init__(self, api_key: str, *, default_user_id: str = "default") -> None:
        if MemoryClient is None:
            raise ImportError("mem0ai 未安装，请先 `pip install mem0ai`")
        self.client = MemoryClient(api_key=api_key)
        self.default_user_id = default_user_id

    def _get_user_id(self, state: Mem0State) -> str:
        return (
            state.get("thread_id")
            or state.get("session_id")
            or self.default_user_id
        )

    def before_agent(self, state: Mem0State, runtime) -> Mem0StateUpdate | None:
        user_id = self._get_user_id(state)
        last_user_msg = ""
        messages = state.get("messages") or []
        for m in reversed(messages):
            if getattr(m, "type", None) == "human":
                last_user_msg = getattr(m, "content", "") or ""
                break

        if not last_user_msg:
            return None

        results = self.client.search(last_user_msg, filters={"user_id": user_id})
        print("results", results)
        return Mem0StateUpdate(mem0_memories=results)

    async def abefore_agent(self, state: Mem0State, runtime) -> Mem0StateUpdate | None:
        # Mem0 客户端是同步的，直接复用同步实现即可
        return self.before_agent(state, runtime)


    def modify_request(self, request: ModelRequest) -> ModelRequest:
        memories = request.state.get("mem0_memories") or []
        
        if not memories:
            return request

        lines = ["## Long-term Memories (from Mem0)"]
        memories = memories["results"]
        for m in memories:
            # Mem0 可能返回 dict，也可能直接返回字符串，这里做兼容处理
            if isinstance(m, dict):
                content = m.get("content") or m.get("memory") or ""
            else:
                content = str(m)
            if content:
                lines.append(f"- {content}")
        extra = "\n".join(lines)
        new_system_message = append_to_system_message(request.system_message, extra)
        return request.override(system_message=new_system_message)

    def wrap_model_call(self, request: ModelRequest, handler):
        modified = self.modify_request(request)
        return handler(modified)

    async def awrap_model_call(self, request: ModelRequest, handler):
        modified = self.modify_request(request)
        return await handler(modified)


    def after_model(self, state: AgentState[Any], runtime) -> AgentState[Any] | None:
        user_id = self._get_user_id(state)
        messages = state.get("messages") or []
        user_texts = [m.content for m in messages if getattr(m, "type", None) == "human"]
        assistant_texts = [m.content for m in messages if getattr(m, "type", None) == "ai"]
        if not user_texts and not assistant_texts:
            return None

        convo: List[Dict[str, str]] = []
        for t in user_texts:
            if t:
                convo.append({"role": "user", "content": t})
        for t in assistant_texts:
            if t:
                convo.append({"role": "assistant", "content": t})

        if convo:
            # 简单写入，不做复杂分类
            self.client.add(convo, user_id=user_id)
        return None

    async def aafter_model(self, state: AgentState[Any], runtime) -> AgentState[Any] | None:
        return self.after_model(state, runtime)

