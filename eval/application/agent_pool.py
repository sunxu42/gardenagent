"""Eval agent lifecycle — per-run AgentManager instances."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from eval.application.agent_client import EvalAgentClient


class EvalAgentFactory:
    """Create isolated eval agent clients; serialize runs when needed."""

    _run_lock = asyncio.Lock()

    @classmethod
    async def create_client(cls) -> EvalAgentClient:
        """Create a fresh AgentManager-backed client for one eval run."""
        return await EvalAgentClient.create()

    @classmethod
    @asynccontextmanager
    async def run_guard(cls):
        """Serialize eval runs to avoid overwhelming shared resources."""
        async with cls._run_lock:
            yield

    @classmethod
    async def reset(cls) -> None:
        """No-op — kept for test compatibility after pool removal."""


# Backward-compatible alias.
EvalAgentPool = EvalAgentFactory
