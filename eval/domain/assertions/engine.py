from __future__ import annotations

from collections.abc import Sequence

from eval.domain.assertions import types as assertion_types
from eval.domain.models import AssertionResult, AssertionStatus, TurnObservation
from eval.domain.scenario import AssertionConfig

_HANDLER_BY_TYPE = {
    "assistant_not_contains": assertion_types.assistant_not_contains,
    "assistant_contains": assertion_types.assistant_contains,
    "assistant_min_length": assertion_types.assistant_min_length,
    "assistant_max_length": assertion_types.assistant_max_length,
    "agent_emotion_in": assertion_types.agent_emotion_in,
    "tool_called": assertion_types.tool_called,
    "tool_not_called": assertion_types.tool_not_called,
    "text_not_matches": assertion_types.text_not_matches,
}


class AssertionEngine:
    """Evaluate L0 assertions against turn observations."""

    def evaluate(
        self,
        observations: Sequence[TurnObservation],
        configs: Sequence[AssertionConfig],
    ) -> tuple[AssertionResult, ...]:
        """Run all configured assertions and return their results."""

        results: list[AssertionResult] = []
        for config in configs:
            handler = _HANDLER_BY_TYPE.get(config.type)
            if handler is None:
                results.append(
                    AssertionResult(
                        name=config.name,
                        status=AssertionStatus.SKIP,
                        message=f"unsupported assertion type: {config.type}",
                    )
                )
                continue
            results.append(handler(observations, config))
        return tuple(results)
