"""Judge integration test guards against provider rate limits."""

from __future__ import annotations

import logging
import os
import time

import pytest

_DEFAULT_SCENARIO_DELAY_SEC = 3.0
_DEFAULT_PER_ATTEMPT_TIMEOUT_SEC = 120

_QUIET_LOGGERS = (
    "deepeval",
    "deepeval.retry",
    "deepeval.retry.openai",
    "deepeval.metrics",
    "httpx",
    "httpcore",
    "openai",
    "mem0",
    "asyncio",
)


def _judge_verbose_enabled() -> bool:
    return os.getenv("EVAL_JUDGE_VERBOSE", "").strip().lower() in {"1", "true", "yes"}


def _configure_deepeval_retries() -> None:
    """Raise DeepEval backoff defaults for flaky 429 responses."""

    os.environ.setdefault("DEEPEVAL_RETRY_MAX_ATTEMPTS", "6")
    os.environ.setdefault("DEEPEVAL_RETRY_INITIAL_SECONDS", "2")
    os.environ.setdefault("DEEPEVAL_RETRY_CAP_SECONDS", "30")
    os.environ.setdefault("DEEPEVAL_RETRY_JITTER", "3")
    os.environ.setdefault(
        "DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE",
        str(_DEFAULT_PER_ATTEMPT_TIMEOUT_SEC),
    )


def _configure_quiet_console() -> None:
    """Suppress DeepEval prompt dumps, progress bars, and retry INFO noise."""

    if _judge_verbose_enabled():
        return

    os.environ.setdefault("DEEPEVAL_VERBOSE_MODE", "0")
    os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "1")

    try:
        from deepeval.utils import set_verbose_mode

        set_verbose_mode(False)
    except Exception:
        pass

    try:
        import deepeval.metrics.conversational_g_eval.conversational_g_eval as conversational_geval

        conversational_geval._debug_print_prompt = lambda *_args, **_kwargs: None
    except Exception:
        pass

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


@pytest.fixture(scope="session", autouse=True)
def _judge_session_defaults() -> None:
    _configure_deepeval_retries()
    _configure_quiet_console()


@pytest.fixture(autouse=True)
def _judge_scenario_pause(request: pytest.FixtureRequest) -> None:
    """Pause between judge scenarios to avoid bursting the eval LLM quota."""

    yield
    if "judge" not in request.keywords:
        return
    raw = os.getenv("EVAL_JUDGE_SCENARIO_DELAY_SEC", str(_DEFAULT_SCENARIO_DELAY_SEC))
    delay = max(0.0, float(raw))
    if delay > 0:
        time.sleep(delay)
