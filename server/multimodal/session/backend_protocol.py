"""Agent session backend port — shared seam for server and eval."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class AgentSessionBackend(Protocol):
    """Narrow interface for agent kernel access from transport and eval."""

    agent_output_queue: asyncio.Queue
    agent_input_queue: asyncio.Queue

    async def achat(
        self,
        user_input: str,
        thread_id: str = "agent-demo",
    ) -> Any:
        """Stream assistant chunks for one user message."""

    async def aclose(self) -> None:
        """Release backend resources."""

    def current_tts_voice(self) -> str | None: ...

    def current_tts_emotion(self) -> tuple[str | None, int]: ...

    def current_vad_metrics(self) -> dict[str, Any] | None: ...

    def baseline_vad(self) -> dict[str, float] | None: ...

    def emotion_ui_profile(self) -> dict[str, Any] | None: ...

    def current_relationship_snapshot(self) -> dict[str, Any] | None: ...

    def vad_snapshot_for_digest(self, digest: str) -> dict[str, Any] | None: ...

    def end_emotion_turn(self) -> None: ...

    def affect_settled_metrics(self) -> dict[str, Any] | None: ...

    def current_tts_prosody(self) -> tuple[int, int, int]: ...

    def set_appraisal_snapshot_listener(
        self,
        listener: Callable[[str], None] | None,
    ) -> None: ...

    def clear_affect_locks(self) -> None: ...

    def set_affect_lock(
        self,
        dimension: str,
        ref_id: str | None,
    ) -> dict[str, Any] | None: ...

    def affect_lock_state(self) -> dict[str, Any] | None: ...
