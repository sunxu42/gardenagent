"""Encode agent output and decode inbound AG-UI WebSocket messages."""

from __future__ import annotations

from typing import Any

from server.agui.types import (
    AGUI_CHANNEL,
    AguiEnvelope,
    a2ui_operations,
    run_error,
    run_finished,
    run_started,
    text_message_content,
    ui_action,
    wrap_event,
)


class AgUIBridge:
    """Bridge between session events and AG-UI multiplex envelopes."""

    def run_started(self, *, run_id: str, message_id: str) -> AguiEnvelope:
        return wrap_event(run_started(message_id=message_id, run_id=run_id))

    def text_delta(self, *, run_id: str, message_id: str, delta: str) -> AguiEnvelope:
        return wrap_event(text_message_content(message_id=message_id, run_id=run_id, delta=delta))

    def run_finished(self, *, run_id: str, message_id: str) -> AguiEnvelope:
        return wrap_event(run_finished(message_id=message_id, run_id=run_id))

    def run_error(self, *, run_id: str, message_id: str, message: str) -> AguiEnvelope:
        return wrap_event(run_error(message_id=message_id, run_id=run_id, message=message))

    def a2ui_operations(
        self,
        *,
        run_id: str,
        message_id: str,
        surface_id: str,
        operations: list[dict[str, Any]],
    ) -> AguiEnvelope:
        return wrap_event(
            a2ui_operations(
                message_id=message_id,
                run_id=run_id,
                surface_id=surface_id,
                operations=operations,
            )
        )

    def parse_inbound(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Return the nested AG-UI event when ``payload`` uses the agui channel."""
        if payload.get("channel") != AGUI_CHANNEL:
            return None
        event = payload.get("event")
        if not isinstance(event, dict):
            return None
        return event

    def on_ui_action(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Validate inbound UI action and normalize shape."""
        if event.get("type") != "UI_ACTION":
            return None
        run_id = str(event.get("runId") or "").strip()
        message_id = str(event.get("messageId") or "").strip()
        surface_id = str(event.get("surfaceId") or "").strip()
        action = event.get("action")
        if not run_id or not message_id or not surface_id or not isinstance(action, dict):
            return None
        return ui_action(
            run_id=run_id,
            message_id=message_id,
            surface_id=surface_id,
            action=action,
        )
