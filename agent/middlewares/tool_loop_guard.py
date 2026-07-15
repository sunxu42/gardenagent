"""拦截同一轮对话内重复的工具调用，避免 ReAct 循环空转。"""

from __future__ import annotations

import json
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import ToolMessage
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.AGENT)

DEFAULT_MAX_IDENTICAL_TOOL_CALLS = 2


def tool_call_signature(tool_call: dict[str, Any]) -> str:
    """Stable fingerprint for a tool invocation."""
    name = str(tool_call.get("name") or "unknown").strip() or "unknown"
    args = tool_call.get("args")
    if not isinstance(args, dict):
        args = {}
    return f"{name}:{json.dumps(args, sort_keys=True, ensure_ascii=False)}"


class ToolLoopGuardState(AgentState):
    pass


class ToolLoopGuardMiddleware(AgentMiddleware[ToolLoopGuardState, Any]):
    """在重复调用达到阈值时短路工具执行，迫使模型改用文字回复。"""

    state_schema = ToolLoopGuardState

    def __init__(self, *, max_identical_calls: int = DEFAULT_MAX_IDENTICAL_TOOL_CALLS) -> None:
        self._max_identical_calls = max(1, max_identical_calls)
        self._signatures: list[str] = []

    def reset_session_state(self) -> None:
        self._signatures = []

    def before_agent(self, state: ToolLoopGuardState, runtime) -> None:
        self._signatures = []

    async def abefore_agent(self, state: ToolLoopGuardState, runtime) -> None:
        self.before_agent(state, runtime)

    def _blocked_message(self, tool_name: str, tool_call_id: str | None) -> ToolMessage:
        return ToolMessage(
            content=(
                "工具调用已跳过：同一工具与参数在本轮对话中已重复多次且未产生新结果。"
                "请勿再次调用相同工具，请根据已有信息直接用文字回复用户。"
            ),
            name=tool_name,
            tool_call_id=tool_call_id or "",
        )

    def _maybe_block(self, tool_call: dict[str, Any]) -> ToolMessage | None:
        signature = tool_call_signature(tool_call)
        identical = sum(1 for item in self._signatures if item == signature)
        if identical < self._max_identical_calls:
            self._signatures.append(signature)
            return None

        tool_name = str(tool_call.get("name") or "unknown")
        tool_call_id = tool_call.get("id")
        _log.warning(
            f"tool loop guard · blocked duplicate call · {tool_name}",
            extra={
                "event": "tool_loop_blocked",
                "tool_name": tool_name,
                "signature": signature,
                "identical_count": identical + 1,
            },
        )
        return self._blocked_message(
            tool_name, tool_call_id if isinstance(tool_call_id, str) else None
        )

    def wrap_tool_call(self, request, handler):
        blocked = self._maybe_block(request.tool_call)
        if blocked is not None:
            return blocked
        return handler(request)

    async def awrap_tool_call(self, request, handler):
        blocked = self._maybe_block(request.tool_call)
        if blocked is not None:
            return blocked
        return await handler(request)
