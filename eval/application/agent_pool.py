from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from eval.application.agent_client import EvalAgentClient


class EvalAgentPool:
    """Process-wide reusable AgentManager for scenario evaluation."""

    _init_lock = asyncio.Lock()
    _run_lock = asyncio.Lock()
    _agent_manager: Any | None = None

    @classmethod
    async def acquire_client(cls) -> tuple[EvalAgentClient, bool]:
        """Return a shared agent client and whether this call performed cold start."""

        async with cls._init_lock:
            cold_start = cls._agent_manager is None
            if cold_start:
                cls._agent_manager = await EvalAgentClient.create_agent_manager()
            client = EvalAgentClient(cls._agent_manager, owns_manager=False)
            return client, cold_start

    @classmethod
    @asynccontextmanager
    async def run_guard(cls):
        """Serialize eval runs against the shared AgentManager instance."""

        async with cls._run_lock:
            yield

    @classmethod
    async def reset(cls) -> None:
        """Release the pooled agent — intended for tests."""

        async with cls._init_lock:
            if cls._agent_manager is None:
                return
            closer = getattr(cls._agent_manager, "aclose", None)
            if callable(closer):
                await closer()
            cls._agent_manager = None
