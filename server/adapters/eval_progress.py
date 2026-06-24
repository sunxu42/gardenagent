"""WebSocket-backed eval progress notifier."""

from __future__ import annotations

from eval.application.ports import EvalProgressNotifier
from server.transport.base import TransportBase


class TransportEvalProgressNotifier:
    """Adapt ``TransportBase`` to ``EvalProgressNotifier``."""

    def __init__(self, transport: TransportBase) -> None:
        self._transport = transport

    async def send_to_client(self, client_id: str, payload: dict[str, object]) -> bool:
        return await self._transport.send_to_client(client_id, payload)


def as_eval_progress_notifier(transport: TransportBase) -> EvalProgressNotifier:
    return TransportEvalProgressNotifier(transport)
