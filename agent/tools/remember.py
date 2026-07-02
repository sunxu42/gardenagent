"""remember tool：显式写入 Mem0 长期记忆。"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)
from pydantic import BaseModel, Field

from langgraph.config import get_config

from agent.memory.mem0.service import Mem0Service


def _user_id_from_runtime() -> str | None:
    try:
        config = get_config()
        tid = config.get("configurable", {}).get("thread_id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
    except RuntimeError:
        pass
    return None


def _truncate(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if max_chars <= 0:
        return ""
    return t if len(t) <= max_chars else (t[: max_chars - 1] + "…")


class RememberInput(BaseModel):
    content: str = Field(description="要记住的用户相关事实或偏好，尽量简短明确。")
    category: str = Field(
        default="preference",
        description="类别：preference / interest / episodic / relationship",
    )


def create_remember_tool(
    service: Mem0Service,
    *,
    debug_log_enabled: bool = False,
    debug_log_max_chars: int = 500,
) -> StructuredTool:
    async def remember(content: str, category: str = "preference") -> dict[str, Any]:
        text = (content or "").strip()
        if not text:
            return {"ok": False, "error": "content 不能为空"}
        uid = _user_id_from_runtime()
        if not uid:
            return {"ok": False, "error": "missing thread_id"}
        try:
            if debug_log_enabled:
                _log.info(
                    f"[mem0:add:remember] embedding_input(user): {_truncate(text, debug_log_max_chars)}",
                )
            result = await service.aadd(
                [{"role": "user", "content": text}],
                user_id=uid,
                metadata={
                    "source": "explicit",
                    "pinned": True,
                    "category": category,
                },
                infer=True,
            )
            _log.info(f"remember tool: {text[:80]}")
            return {"ok": True, "result": result}
        except Exception as e:
            _log.warning(f"remember tool failed: {e!r}")
            return {"ok": False, "error": repr(e)}

    return StructuredTool.from_function(
        name="remember",
        description=(
            "将用户明确要求记住的事实写入长期记忆（Mem0）。"
            "当用户说「记住」「别忘了」或表达持久偏好时使用。"
        ),
        coroutine=remember,
        args_schema=RememberInput,
    )
