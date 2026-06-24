from __future__ import annotations

from collections.abc import Sequence

from deepeval.test_case import ConversationalTestCase, Turn

from eval.domain.models import TurnObservation


def to_conversational_test_case(
    observations: Sequence[TurnObservation],
    *,
    scenario: str | None = None,
) -> ConversationalTestCase:
    """Convert internal turn observations to a DeepEval conversational test case."""

    turns: list[Turn] = []
    for item in observations:
        turns.append(Turn(role="user", content=item.user_text))
        turns.append(Turn(role="assistant", content=item.assistant_text))
    return ConversationalTestCase(scenario=scenario, turns=turns)
