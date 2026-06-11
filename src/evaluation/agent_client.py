from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Protocol, cast

from src.eval_api.schemas import AgentAffectSnapshot
from yard.yard_manage import YardManager


class _YardManagerProtocol(Protocol):
    async def achat(
        self,
        user_input: str,
        *,
        thread_id: str,
    ) -> AsyncIterator[Mapping[str, object]]:
        """Stream assistant chunks for one user message."""

    async def aclose(self) -> None:
        """Release YardManager resources."""


class YardAgentClient:
    """Adapts YardManager to the evaluation session agent-client interface."""

    def __init__(self, yard_manager: _YardManagerProtocol) -> None:
        """Initialize the client with an existing YardManager instance."""

        self._yard_manager = yard_manager

    @classmethod
    async def create(cls) -> YardAgentClient:
        """Create a client backed by a fully initialized YardManager."""

        yard_manager = await YardManager.create()
        return cls(yard_manager)

    async def respond(
        self,
        message: str,
        thread_id: str,
    ) -> tuple[str, AgentAffectSnapshot | None]:
        """Return assistant text and a best-effort affect snapshot."""

        chunks: list[str] = []
        async for chunk in self._yard_manager.achat(message, thread_id=thread_id):
            content = chunk.get("content")
            if isinstance(content, str):
                chunks.append(content)

        return "".join(chunks).strip(), self._affect_snapshot()

    async def aclose(self) -> None:
        """Release YardManager resources after an evaluation run."""

        await self._yard_manager.aclose()

    def _affect_snapshot(self) -> AgentAffectSnapshot | None:
        """Capture public YardManager affect data when available."""

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
        helper = getattr(self._yard_manager, "current_tts_emotion", None)
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
        helper = getattr(self._yard_manager, "current_vad_metrics", None)
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
        helper = getattr(self._yard_manager, "current_relationship_snapshot", None)
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
