"""按 user_id 清空 Mem0/FAISS、LangGraph checkpoint 与运行时会话缓冲。"""

from __future__ import annotations

import asyncio
from typing import Any
from weakref import WeakSet

from agent.observability.logging import LogModule, get_logger
from agent.observability.logging.context import bind_session

_log = get_logger(LogModule.SYSTEM)

from agent.memory.core.user_id import normalize_user_id

_agent_managers: WeakSet[Any] = WeakSet()


def register_agent_manager(agent_manager: Any) -> None:
    _agent_managers.add(agent_manager)


def register_yard_manager(agent_manager: Any) -> None:
    """Deprecated alias for :func:`register_agent_manager`."""
    register_agent_manager(agent_manager)


def _clear_session_buffers(user_id: str) -> int:
    count = 0
    for manager in list(_agent_managers):
        buf = getattr(manager, "session_buffer", None)
        if buf is not None and hasattr(buf, "clear_thread"):
            buf.clear_thread(user_id)
            count += 1
    return count


def _clear_emotion_state() -> int:
    """重置所有已注册 AgentManager 的运行时情绪与持久化状态。"""
    count = 0
    for manager in list(_agent_managers):
        reset_fn = getattr(manager, "reset_emotion_state", None)
        if not callable(reset_fn):
            continue
        try:
            if reset_fn():
                count += 1
        except Exception as e:
            _log.warning(f"emotion reset failed: {e!r}")
    return count


async def _clear_checkpoints(user_id: str) -> int:
    count = 0
    config = {"configurable": {"thread_id": user_id}}
    for manager in list(_agent_managers):
        cp = getattr(manager, "_checkpointer", None)
        if cp is None:
            continue
        try:
            if hasattr(cp, "adelete_thread"):
                await cp.adelete_thread(config)
            elif hasattr(cp, "delete_thread"):
                await asyncio.to_thread(cp.delete_thread, config)
            count += 1
        except Exception as e:
            _log.warning(f"delete_thread failed for {user_id}: {e!r}")
    return count


def _clear_mem0(user_id: str) -> dict[str, Any]:
    from shared.config.resolve_agent import resolve_agent_runtime
    from agent.configs.secrets import load_secrets
    from agent.configs.settings import load_settings
    from agent.memory.mem0.service import Mem0Service

    cfg = resolve_agent_runtime(load_settings(), load_secrets())
    if not cfg.memory_enabled:
        return {"skipped": True, "reason": "memory_disabled"}
    service = Mem0Service.create(cfg)
    service.delete_all_for_user(user_id)
    return {"cleared": True}


def _summarize_clear_result(result: dict[str, Any]) -> str:
    mem0 = result.get("mem0")
    if isinstance(mem0, dict):
        if mem0.get("skipped"):
            mem0_part = "Mem0 跳过"
        elif mem0.get("cleared"):
            mem0_part = "Mem0 已清"
        elif mem0.get("error"):
            mem0_part = "Mem0 失败"
        else:
            mem0_part = "Mem0 未知"
    else:
        mem0_part = "Mem0 —"
    checkpoints = int(result.get("checkpoints") or 0)
    buffers = int(result.get("session_buffers") or 0)
    emotion = result.get("emotion")
    emotion_n = 0
    if isinstance(emotion, dict):
        emotion_n = int(emotion.get("reset_managers") or 0)
    return (
        f"用户数据已清空（{mem0_part}；checkpoint×{checkpoints}；"
        f"session_buffer×{buffers}；emotion_reset×{emotion_n}）"
    )


def _log_user_data_cleared(user_id: str, result: dict[str, Any]) -> None:
    """写入 jsonl，并在 WebSocket 会话仍在线时推送到前端日志面板。"""
    message = _summarize_clear_result(result)
    with bind_session(user_id):
        _log.info(
            message,
            action="clear_user_data",
            user_id=user_id,
            mem0=result.get("mem0"),
            checkpoints=result.get("checkpoints"),
            session_buffers=result.get("session_buffers"),
            emotion=result.get("emotion"),
        )


async def clear_user_data(user_id: str) -> dict[str, Any]:
    uid = normalize_user_id(user_id)
    result: dict[str, Any] = {"user_id": uid}

    try:
        result["mem0"] = await asyncio.to_thread(_clear_mem0, uid)
    except Exception as e:
        _log.warning(f"Mem0 clear failed: {e!r}")
        result["mem0"] = {"cleared": False, "error": str(e)}

    result["session_buffers"] = _clear_session_buffers(uid)
    result["checkpoints"] = await _clear_checkpoints(uid)
    result["emotion"] = {"reset_managers": _clear_emotion_state()}
    _log_user_data_cleared(uid, result)
    return result
