"""Detect A2UI surfaces that must stay open until the user interacts."""

from __future__ import annotations

from typing import Any

INTERACTIVE_A2UI_SURFACES = frozenset({
    "single-select",
    "single-select-binary",
    "single-select-emoji",
    "single-select-cards",
    "multi-select",
    "date-picker",
    "data-table-select",
    # Legacy surfaces kept for stored / mid-migration sessions.
    "plan-selector",
    "binary-choice",
    "emoji-picker",
})
PLAN_OPTION_CARD_COMPONENT = "PlanOptionCard"
MULTI_SELECT_OPTION_COMPONENT = "MultiSelectOption"
BINARY_CHOICE_BUTTON_COMPONENT = "BinaryChoiceButton"
EMOJI_OPTION_COMPONENT = "EmojiOption"
SINGLE_SELECT_OPTION_COMPONENT = "SingleSelectOption"
DATA_TABLE_ROW_OPTION_COMPONENT = "DataTableRowOption"
DATE_PICKER_COMPONENT = "DatePicker"


def surface_requires_ui_interaction(surface_id: str, operations: list[dict[str, Any]]) -> bool:
    """Return True when the client should remain interactive after the agent turn ends."""
    if surface_id.strip() in INTERACTIVE_A2UI_SURFACES:
        return True
    interactive_components = {
        PLAN_OPTION_CARD_COMPONENT,
        MULTI_SELECT_OPTION_COMPONENT,
        BINARY_CHOICE_BUTTON_COMPONENT,
        EMOJI_OPTION_COMPONENT,
        SINGLE_SELECT_OPTION_COMPONENT,
        DATA_TABLE_ROW_OPTION_COMPONENT,
        DATE_PICKER_COMPONENT,
    }
    for operation in operations:
        update = operation.get("updateComponents")
        if not isinstance(update, dict):
            continue
        components = update.get("components")
        if not isinstance(components, list):
            continue
        for component in components:
            if isinstance(component, dict) and component.get("component") in interactive_components:
                return True
    return False
