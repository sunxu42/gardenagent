from __future__ import annotations

from collections.abc import Sequence

from eval.domain.models import TurnObservation
from eval.domain.scenario import ScenarioFixture, UserDriverConfig


class ScriptedUser:
    """Returns fixed user utterances for scripted evaluation scenarios."""

    def __init__(self, config: UserDriverConfig) -> None:
        self._config = config

    async def generate_turn(
        self,
        scenario: ScenarioFixture,
        history: Sequence[TurnObservation],
        round_index: int,
    ) -> str:
        """Return the scripted user message for the requested round."""

        del scenario, history
        index = round_index - 1
        if index < 0 or index >= len(self._config.turns):
            raise IndexError(f"scripted turn out of range: {round_index}")
        return self._config.turns[index].text
