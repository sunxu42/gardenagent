"""记忆子系统装配与后台任务：由 YardManager.create / aclose 调用。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from yard.memory.core.buffer import SessionBuffer
from yard.memory.mem0.service import Mem0Service
from yard.memory.runtime.flush import (
    flush_agent_session_memory,
    run_memory_idle_flush_loop,
)
from yard.middlewares.mem0_oss_middleware import Mem0OssMiddleware
from yard.middlewares.mem0_summarization_flush_middleware import Mem0SummarizationFlushMiddleware
from yard.tools.remember import create_remember_tool


@dataclass
class MemorySubsystem:
    mem0_service: Mem0Service | None = None
    session_buffer: SessionBuffer | None = None
    middleware: list[Any] = field(default_factory=list)
    extra_tools: list[Any] = field(default_factory=list)


def setup_memory_subsystem(config, agent_holder: Any) -> MemorySubsystem:
    """按配置构建 Mem0 服务、middleware 与 remember 工具；失败时返回空子系统。"""
    if not config.memory_enabled:
        return MemorySubsystem()

    try:
        mem0_service = Mem0Service.create(config)
        session_buffer = SessionBuffer()
        middleware = [
            Mem0OssMiddleware(mem0_service, config, session_buffer=session_buffer),
            Mem0SummarizationFlushMiddleware(agent_holder),
        ]
        extra_tools = [
            create_remember_tool(
                mem0_service,
                debug_log_enabled=config.memory_debug_log_enabled,
                debug_log_max_chars=config.memory_debug_log_max_chars,
            )
        ]
        return MemorySubsystem(
            mem0_service=mem0_service,
            session_buffer=session_buffer,
            middleware=middleware,
            extra_tools=extra_tools,
        )
    except ImportError as e:
        print(f"[warn] Mem0 memory disabled: {e}")
        return MemorySubsystem()
    except Exception as e:
        print(f"[warn] Mem0 memory init failed: {e}")
        return MemorySubsystem()


def init_memory_runtime_state(yard_manager: Any) -> None:
    """初始化记忆子系统运行期状态（空闲 flush 用）。"""
    yard_manager._memory_last_turn_finished_at = None
    yard_manager._memory_flush_stop = asyncio.Event()
    yard_manager._memory_flush_task = None


def start_memory_background_tasks(yard_manager: Any) -> None:
    """启动会话空闲 flush 后台循环（配置允许且 Mem0 已启用时）。"""
    init_memory_runtime_state(yard_manager)

    idle_sec = int(getattr(yard_manager.config, "memory_session_flush_idle_sec", 0) or 0)
    if yard_manager.mem0_service is None or idle_sec <= 0:
        return

    poll_sec = float(
        getattr(yard_manager.config, "memory_session_flush_poll_sec", 30) or 30
    )
    yard_manager._memory_flush_task = asyncio.create_task(
        run_memory_idle_flush_loop(
            agent=yard_manager,
            idle_sec=float(idle_sec),
            poll_sec=poll_sec,
            stop_event=yard_manager._memory_flush_stop,
        ),
        name="memory_idle_flush_loop",
    )


async def shutdown_memory_subsystem(yard_manager: Any) -> None:
    """进程退出前 flush 会话记忆并停止后台任务。"""
    if getattr(yard_manager.config, "memory_session_flush_on_shutdown", True):
        try:
            await flush_agent_session_memory(yard_manager, flush_reason="shutdown")
        except Exception:
            pass

    mem_stop = getattr(yard_manager, "_memory_flush_stop", None)
    if mem_stop is not None:
        mem_stop.set()

    mem_task = getattr(yard_manager, "_memory_flush_task", None)
    if mem_task is not None and not mem_task.done():
        mem_task.cancel()
        try:
            await mem_task
        except asyncio.CancelledError:
            pass
