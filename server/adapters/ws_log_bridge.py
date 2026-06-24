from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from shared.observability.logging import register_session_emitter, unregister_session_emitter

TransportSend = Callable[[str], Awaitable[None]]


def attach_session_logging(session_id: str, send_json: TransportSend) -> None:
    async def emitter(payload: dict[str, Any]) -> None:
        await send_json(json.dumps(payload))

    register_session_emitter(session_id, emitter)


def detach_session_logging(session_id: str) -> None:
    unregister_session_emitter(session_id)
