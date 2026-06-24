"""Uvicorn entry point for the unified Garden server."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from shared.config.resolve_server import resolve_server_runtime
from shared.config.server import load_settings
from shared.observability.logging import configure_logging


def main() -> None:
    cfg = resolve_server_runtime(load_settings())
    configure_logging()
    uvicorn.run(
        "server.app:app",
        host=cfg.host,
        port=cfg.port,
        log_level="info",
        ws="websockets-sansio",
    )


if __name__ == "__main__":
    main()
