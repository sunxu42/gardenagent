"""Unified Starlette application: WebSocket transport + prompt editor HTTP API."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from shared.config.resolve_server import resolve_server_runtime
from shared.config.server import load_settings
from eval.api.routes import create_eval_routes
from eval.application.job_manager import EvalJobManager
from server.handler.handler_manager import HandlerManager
from prompt_editor.api.routes import create_prompt_editor_routes
from server.transport import WebSocketTransport

from shared.config.paths import resolve_prompts_dir

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_ROOT = resolve_prompts_dir()


def create_app() -> Starlette:
    """Build the unified server with WebSocket and prompt-editor routes."""
    settings = load_settings()
    cfg = resolve_server_runtime(settings)
    transport = WebSocketTransport(host=cfg.host, port=cfg.port)
    job_manager = EvalJobManager(transport)
    handler_manager = HandlerManager(transport, cfg.handler_type, cfg)

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
        *create_eval_routes(job_manager),
        WebSocketRoute("/ws", ws_endpoint),
    ]
    app = Starlette(routes=routes, lifespan=lifespan)
    return app


app = create_app()
