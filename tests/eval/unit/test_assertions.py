from eval.domain.assertions.engine import AssertionEngine
from eval.domain.models import TurnObservation
from eval.domain.scenario import AssertionConfig


def test_assistant_not_contains_fails_on_forbidden_word() -> None:
    engine = AssertionEngine()
    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="我是蛋黄"),
        TurnObservation(round=2, user_text="u", assistant_text="我是语言模型"),
    )
    configs = (
        AssertionConfig(
            type="assistant_not_contains",
            name="no_ai",
            forbidden=["语言模型"],
        ),
    )
    results = engine.evaluate(observations, configs)
    assert results[0].status.value == "fail"


def test_assistant_contains_any_round() -> None:
    engine = AssertionEngine()
    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="你好"),
        TurnObservation(round=2, user_text="u", assistant_text="我是蛋黄"),
    )
    configs = (
        AssertionConfig(
            type="assistant_contains",
            name="mentions_name",
            required=["蛋黄"],
            any_round=True,
        ),
    )
    results = engine.evaluate(observations, configs)
    assert results[0].status.value == "pass"


def test_tool_called_optional_warns_when_missing() -> None:
    engine = AssertionEngine()
    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="ok", raw_updates=()),
    )
    configs = (
        AssertionConfig(
            type="tool_called",
            name="status_tool",
            tool_name="session_status",
            optional=True,
        ),
    )
    results = engine.evaluate(observations, configs)
    assert results[0].status.value == "warn"


def test_assistant_max_length_fails_when_too_long() -> None:
    engine = AssertionEngine()
    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="短回复。"),
        TurnObservation(round=2, user_text="u", assistant_text="x" * 121),
    )
    configs = (
        AssertionConfig(
            type="assistant_max_length",
            name="concise_reply",
            max_chars=120,
        ),
    )
    results = engine.evaluate(observations, configs)
    assert results[0].status.value == "fail"
    assert "round 2" in results[0].message


def test_assistant_max_length_passes_within_limit() -> None:
    engine = AssertionEngine()
    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="嗯，我听到了。"),
    )
    configs = (
        AssertionConfig(
            type="assistant_max_length",
            name="concise_reply",
            max_chars=120,
        ),
    )
    results = engine.evaluate(observations, configs)
    assert results[0].status.value == "pass"


def test_assistant_max_length_skips_when_unconfigured() -> None:
    from eval.domain.assertions import types as assertion_types

    observations = (
        TurnObservation(round=1, user_text="u", assistant_text="任意长度" * 50),
    )
    config = AssertionConfig(type="assistant_max_length", name="concise_reply")
    result = assertion_types.assistant_max_length(observations, config)
    assert result.status.value == "skip"
