"""按 user_id 清空 Mem0/FAISS、LangGraph checkpoint 与运行时会话缓冲。"""

from __future__ import annotations

import asyncio
from typing import Any
from weakref import WeakSet

from loguru import logger

from yard.memory.core.user_id import normalize_user_id

_yard_managers: WeakSet[Any] = WeakSet()


def register_yard_manager(yard_manager: Any) -> None:
    _yard_managers.add(yard_manager)


def _clear_session_buffers(user_id: str) -> int:
    count = 0
    for ym in list(_yard_managers):
        buf = getattr(ym, "session_buffer", None)
        if buf is not None and hasattr(buf, "clear_thread"):
            buf.clear_thread(user_id)
            count += 1
    return count


async def _clear_checkpoints(user_id: str) -> int:
    count = 0
    config = {"configurable": {"thread_id": user_id}}
    for ym in list(_yard_managers):
        cp = getattr(ym, "_checkpointer", None)
        if cp is None:
            continue
        try:
            if hasattr(cp, "adelete_thread"):
                await cp.adelete_thread(config)
            elif hasattr(cp, "delete_thread"):
                await asyncio.to_thread(cp.delete_thread, config)
            count += 1
        except Exception as e:
            logger.warning("delete_thread failed for {}: {!r}", user_id, e)
    return count


def _clear_mem0(user_id: str) -> dict[str, Any]:
    from yard.configs.config import load_config
    from yard.memory.mem0.service import Mem0Service

    cfg = load_config()
    if not cfg.memory_enabled:
        return {"skipped": True, "reason": "memory_disabled"}
    service = Mem0Service.create(cfg)
    service.delete_all_for_user(user_id)
    return {"cleared": True}


async def clear_user_data(user_id: str) -> dict[str, Any]:
    uid = normalize_user_id(user_id)
    result: dict[str, Any] = {"user_id": uid}

    try:
        result["mem0"] = await asyncio.to_thread(_clear_mem0, uid)
    except Exception as e:
        logger.warning("Mem0 clear failed: {!r}", e)
        result["mem0"] = {"cleared": False, "error": str(e)}

    result["session_buffers"] = _clear_session_buffers(uid)
    result["checkpoints"] = await _clear_checkpoints(uid)
    return result
