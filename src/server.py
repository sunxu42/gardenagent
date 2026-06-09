"""Uvicorn entry point for the unified Garden server."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from src.config import load_config
from src.log import setup_logger


def main() -> None:
    cfg = load_config()
    setup_logger(
        log_file=cfg.logging.log_file,
        log_level=cfg.logging.log_level,
        disable_modules=cfg.logging.disable_modules,
    )
    uvicorn.run(
        "src.app:app",
        host=cfg.host,
        port=cfg.port,
        log_level="info",
        ws="websockets-sansio",
    )


if __name__ == "__main__":
    main()
