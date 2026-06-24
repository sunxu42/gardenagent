import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.transport.transport import WebSocketTransport


@pytest.mark.asyncio
async def test_send_data_serializes_dict_as_json() -> None:
    transport = WebSocketTransport()
    websocket = MagicMock()
    websocket.send_text = AsyncMock()

    await transport._send_data(websocket, {"type": "eval_started", "run_id": "eval_x"})

    websocket.send_text.assert_awaited_once()
    payload = json.loads(websocket.send_text.await_args.args[0])
    assert payload["type"] == "eval_started"
    assert payload["run_id"] == "eval_x"
