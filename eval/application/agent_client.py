from __future__ import annotations

import time
from collections.abc import AsyncIterator, Mapping
from typing import Protocol, cast

from eval.api.schemas import AgentAffectSnapshot
from agent.manager import AgentManager


class _AgentManagerProtocol(Protocol):
    async def achat(
        self,
        user_input: str,
        *,
        thread_id: str,
    ) -> AsyncIterator[Mapping[str, object]]:
        """Stream assistant chunks for one user message."""

    async def aclose(self) -> None:
        """Release AgentManager resources."""


class EvalAgentClient:
    """Adapts AgentManager to the evaluation session agent-client interface."""

    def __init__(
        self,
        agent_manager: _AgentManagerProtocol,
        *,
        owns_manager: bool = False,
    ) -> None:
        """Initialize the client with an existing AgentManager instance."""

        self._agent_manager = agent_manager
        self._owns_manager = owns_manager

    @classmethod
    async def create_agent_manager(cls) -> _AgentManagerProtocol:
        """Create a standalone AgentManager for one-off evaluation sessions."""

        agent_manager = await AgentManager.create()
        return agent_manager

    @classmethod
    async def create_yard_manager(cls) -> _AgentManagerProtocol:
        """Deprecated alias for :meth:`create_agent_manager`."""
        return await cls.create_agent_manager()

    @classmethod
    async def create(cls) -> EvalAgentClient:
        """Create a client backed by a fully initialized AgentManager."""

        agent_manager = await cls.create_agent_manager()
        return cls(agent_manager, owns_manager=True)

    async def respond(
        self,
        message: str,
        thread_id: str,
    ) -> tuple[str, AgentAffectSnapshot | None]:
        """Return assistant text and a best-effort affect snapshot."""

        text, affect, _, _ = await self.respond_with_observation(message, thread_id)
        return text, affect

    async def respond_with_observation(
        self,
        message: str,
        thread_id: str,
    ) -> tuple[str, AgentAffectSnapshot | None, tuple[str, ...], float]:
        """Return assistant text, affect snapshot, raw updates, and latency in ms."""

        started = time.perf_counter()
        chunks: list[str] = []
        updates: list[str] = []
        async for chunk in self._agent_manager.achat(message, thread_id=thread_id):
            content = chunk.get("content")
            if isinstance(content, str):
                chunks.append(content)
            update = chunk.get("updates")
            if isinstance(update, str):
                updates.append(update)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return "".join(chunks).strip(), self._affect_snapshot(), tuple(updates), latency_ms

    async def aclose(self) -> None:
        """Release AgentManager resources after an evaluation run."""

        if not self._owns_manager:
            return
        await self._agent_manager.aclose()

    def _affect_snapshot(self) -> AgentAffectSnapshot | None:
        """Capture public AgentManager affect data when available."""

        emotion = self._current_emotion()
        vad = self._current_vad()
        relationship_stage = self._current_relationship_stage()

        if emotion is None and vad is None and relationship_stage is None:
            return None

        return AgentAffectSnapshot(
            emotion=emotion,
            vad=vad,
            relationship_stage=relationship_stage,
        )

    def _current_emotion(self) -> str | None:
        helper = getattr(self._agent_manager, "current_tts_emotion", None)
        if not callable(helper):
            return None

        try:
            result = helper()
        except Exception:
            return None

        if not isinstance(result, tuple) or not result:
            return None

        emotion = result[0]
        return emotion if isinstance(emotion, str) else None

    def _current_vad(self) -> dict[str, float] | None:
        helper = getattr(self._agent_manager, "current_vad_metrics", None)
        if not callable(helper):
            return None

        try:
            result = helper()
        except Exception:
            return None

        if not isinstance(result, Mapping):
            return None

        vad = result.get("agent_vad_after")
        if not isinstance(vad, dict):
            return None

        return cast(dict[str, float], vad)

    def _current_relationship_stage(self) -> str | None:
        helper = getattr(self._agent_manager, "current_relationship_snapshot", None)
        if not callable(helper):
            return None

        try:
            result = helper()
        except Exception:
            return None

        if not isinstance(result, Mapping):
            return None

        stage = result.get("stage")
        return stage if isinstance(stage, str) else None


# Backward-compatible alias.
YardAgentClient = EvalAgentClient
