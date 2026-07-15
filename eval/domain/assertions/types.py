from __future__ import annotations

import re
from collections.abc import Sequence

from eval.domain.models import AssertionResult, AssertionStatus, TurnObservation
from eval.domain.scenario import AssertionConfig


def assistant_not_contains(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when any assistant reply contains a forbidden substring."""

    for observation in observations:
        for forbidden in config.forbidden:
            if forbidden in observation.assistant_text:
                return AssertionResult(
                    name=config.name,
                    status=AssertionStatus.FAIL,
                    message=f"round {observation.round} contains forbidden text: {forbidden}",
                    expected=config.forbidden,
                    actual=observation.assistant_text,
                )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="no forbidden text found",
    )


def assistant_contains(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Pass when required substrings appear in assistant replies."""

    if not config.required:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no required substrings configured",
        )

    if config.any_round:
        combined = "\n".join(item.assistant_text for item in observations)
        missing = [item for item in config.required if item not in combined]
        if missing:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"missing required substrings: {missing}",
                expected=config.required,
                actual=combined,
            )
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.PASS,
            message="all required substrings found",
        )

    for observation in observations:
        missing = [
            item for item in config.required if item not in observation.assistant_text
        ]
        if missing:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"round {observation.round} missing required substrings: {missing}",
                expected=config.required,
                actual=observation.assistant_text,
            )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="all required substrings found in every round",
    )


def assistant_min_length(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when any assistant reply is shorter than min_chars."""

    min_chars = config.min_chars or 0
    for observation in observations:
        if len(observation.assistant_text) < min_chars:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=(
                    f"round {observation.round} reply too short: "
                    f"{len(observation.assistant_text)} < {min_chars}"
                ),
                expected=min_chars,
                actual=len(observation.assistant_text),
            )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="all replies meet minimum length",
    )


def assistant_max_length(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when any assistant reply exceeds max_chars."""

    max_chars = config.max_chars
    if max_chars is None:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no max_chars configured",
        )

    for observation in observations:
        length = len(observation.assistant_text)
        if length > max_chars:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=(
                    f"round {observation.round} reply too long: "
                    f"{length} > {max_chars}"
                ),
                expected=max_chars,
                actual=length,
            )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="all replies within maximum length",
    )


def agent_emotion_in(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when agent affect emotion is outside the allowed set."""

    allowed = set(config.allowed)
    if not allowed:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no allowed emotions configured",
        )

    for observation in observations:
        emotion = (
            observation.agent_affect.emotion
            if observation.agent_affect is not None
            else None
        )
        if emotion is None:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"round {observation.round} missing agent affect emotion",
                expected=sorted(allowed),
                actual=None,
            )
        if emotion not in allowed:
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"round {observation.round} emotion not allowed: {emotion}",
                expected=sorted(allowed),
                actual=emotion,
            )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="all emotions are within allowed set",
    )


def tool_called(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Pass when the configured tool name appears in raw updates."""

    tool_name = config.tool_name
    if not tool_name:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no tool_name configured",
        )

    for observation in observations:
        if any(tool_name in update for update in observation.raw_updates):
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.PASS,
                message=f"tool called: {tool_name}",
            )

    status = AssertionStatus.WARN if config.optional else AssertionStatus.FAIL
    return AssertionResult(
        name=config.name,
        status=status,
        message=f"tool not called: {tool_name}",
        expected=tool_name,
        actual=[update for item in observations for update in item.raw_updates],
    )


def tool_not_called(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when the configured tool name appears in raw updates."""

    tool_name = config.tool_name
    if not tool_name:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no tool_name configured",
        )

    for observation in observations:
        if any(tool_name in update for update in observation.raw_updates):
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"tool was called but should not be: {tool_name}",
                expected=f"not {tool_name}",
                actual=list(observation.raw_updates),
            )

    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message=f"tool not called: {tool_name}",
    )


def text_not_matches(
    observations: Sequence[TurnObservation],
    config: AssertionConfig,
) -> AssertionResult:
    """Fail when assistant reply matches a forbidden regex pattern."""

    if not config.pattern:
        return AssertionResult(
            name=config.name,
            status=AssertionStatus.SKIP,
            message="no pattern configured",
        )

    regex = re.compile(config.pattern, re.MULTILINE)
    for observation in observations:
        if regex.search(observation.assistant_text):
            return AssertionResult(
                name=config.name,
                status=AssertionStatus.FAIL,
                message=f"round {observation.round} matched forbidden pattern",
                expected=config.pattern,
                actual=observation.assistant_text,
            )
    return AssertionResult(
        name=config.name,
        status=AssertionStatus.PASS,
        message="pattern not matched",
    )
