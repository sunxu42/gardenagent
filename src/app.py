"""Unified Starlette application: WebSocket transport + prompt editor HTTP API."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from src.config import load_config
from src.eval_api.routes import create_eval_routes
from src.handler_layer.handler_manager import HandlerManager
from src.prompt_editor_api.prompt_editor_routes import create_prompt_editor_routes
from src.transport_layer import WebSocketTransport

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_ROOT = REPO_ROOT / "yard" / "prompts"


def create_app() -> Starlette:
    """Build the unified server with WebSocket and prompt-editor routes."""
    cfg = load_config()
    transport = WebSocketTransport(host=cfg.host, port=cfg.port)
    handler_manager = HandlerManager(transport, cfg.handler_type)

    transport.register_connection_handler(
        on_connect=handler_manager.create_or_reuse_handler,
        on_disconnect=handler_manager.remove_handler,
    )
    transport.register_message_handler(handler_manager.handle_message)

    async def ws_endpoint(websocket: WebSocket) -> None:
        await transport.handle_starlette_connection(websocket)

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        await handler_manager.start()
        transport._is_running = True
        try:
            yield
        finally:
            await handler_manager.stop()
            await transport.stop()

    routes = [
        *create_prompt_editor_routes(PROMPTS_ROOT),
        *create_eval_routes(),
        WebSocketRoute("/ws", ws_endpoint),
    ]
    return Starlette(routes=routes, lifespan=lifespan)


app = create_app()
