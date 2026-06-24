import asyncio
from pathlib import Path

import pytest

from eval.domain.progress import EvalProgressEvent
from eval.domain.runner import EvalRunner
from eval.domain.scenario import load_scenario
from tests.eval.paths import SCENARIOS_DIR


class _FakeAgent:
    async def respond_with_observation(self, message: str, thread_id: str):
        return f"reply:{message}", None, (), 1.0

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_runner_emits_turn_progress() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    events: list[EvalProgressEvent] = []

    async def on_progress(event: EvalProgressEvent) -> None:
        events.append(event)

    result = await EvalRunner(
        agent_client=_FakeAgent(),
        judge_runner=None,
    ).run_scenario(
        scenario,
        progress_callback=on_progress,
    )
    assert result.status == "completed"
    assert any(event.type == "eval_started" for event in events)
    assert any(event.type == "eval_turn" for event in events)
    assert any(event.type == "eval_assertions" for event in events)
    assert any(event.type == "eval_completed" for event in events)


@pytest.mark.asyncio
async def test_runner_honours_cancel_event() -> None:
    scenario = load_scenario(SCENARIOS_DIR / "smoke/greeting_01.yaml")
    cancel_event = asyncio.Event()
    cancel_event.set()
    events: list[EvalProgressEvent] = []

    async def on_progress(event: EvalProgressEvent) -> None:
        events.append(event)

    result = await EvalRunner(
        agent_client=_FakeAgent(),
        judge_runner=None,
    ).run_scenario(
        scenario,
        progress_callback=on_progress,
        cancel_event=cancel_event,
    )
    assert result.status == "cancelled"
    assert result.observations == ()
    assert any(event.type == "eval_cancelled" for event in events)
