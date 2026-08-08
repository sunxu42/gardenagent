"""Unified observability bootstrap."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.observability.logging import configure_logging as _configure_logging
from shared.observability.logging.sinks.websocket import WebSessionSink

if TYPE_CHECKING:
    from shared.config.secrets import Secrets


def configure_observability(secrets: Secrets | None = None) -> WebSessionSink:
    """Initialize structured logging (and honor ``GARDEN_LOG_DIR`` when set)."""
    return _configure_logging(secrets)
