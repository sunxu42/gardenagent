"""Eval application ports (dependency inversion)."""

from __future__ import annotations

from typing import Protocol


class EvalProgressNotifier(Protocol):
    """Push eval progress events to a connected client."""

    async def send_to_client(self, client_id: str, payload: dict[str, object]) -> bool:
        """Send a payload; return whether delivery succeeded."""

