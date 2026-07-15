"""AG-UI event types and WebSocket envelope helpers."""

from __future__ import annotations

from typing import Any, TypedDict

AGUI_CHANNEL = "agui"


class AguiEnvelope(TypedDict):
    channel: str
    event: dict[str, Any]


def wrap_event(event: dict[str, Any]) -> AguiEnvelope:
    """Wrap a raw AG-UI event in the multiplex channel envelope."""
    return {"channel": AGUI_CHANNEL, "event": event}


def run_started(*, message_id: str, run_id: str) -> dict[str, Any]:
    return {
        "type": "RUN_STARTED",
        "messageId": message_id,
        "runId": run_id,
    }


def text_message_content(*, message_id: str, run_id: str, delta: str) -> dict[str, Any]:
    return {
        "type": "TEXT_MESSAGE_CONTENT",
        "messageId": message_id,
        "runId": run_id,
        "delta": delta,
    }


def run_finished(*, message_id: str, run_id: str) -> dict[str, Any]:
    return {
        "type": "RUN_FINISHED",
        "messageId": message_id,
        "runId": run_id,
    }


def run_error(*, message_id: str, run_id: str, message: str) -> dict[str, Any]:
    return {
        "type": "RUN_ERROR",
        "messageId": message_id,
        "runId": run_id,
        "message": message,
    }


def a2ui_operations(
    *,
    message_id: str,
    run_id: str,
    surface_id: str,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "A2UI_OPERATIONS",
        "messageId": message_id,
        "runId": run_id,
        "surfaceId": surface_id,
        "operations": operations,
    }


def ui_action(
    *,
    run_id: str,
    message_id: str,
    surface_id: str,
    action: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "UI_ACTION",
        "runId": run_id,
        "messageId": message_id,
        "surfaceId": surface_id,
        "action": action,
    }
