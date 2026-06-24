import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval.application.job_manager import EvalJobConflictError, EvalJobManager


def _notifier() -> MagicMock:
    notifier = MagicMock()
    notifier.send_to_client = AsyncMock(return_value=True)
    return notifier


@pytest.mark.asyncio
async def test_start_returns_run_id_immediately() -> None:
    notifier = _notifier()
    manager = EvalJobManager(notifier=notifier)

    async def fake_execute(
        run_id: str,
        scenario_id: str,
        client_id: str,
        cancel_event: asyncio.Event,
    ) -> None:
        try:
            await asyncio.sleep(0.05)
        finally:
            manager._cleanup_run(run_id, client_id)

    manager._execute_scenario = fake_execute  # type: ignore[method-assign]

    run_id = await manager.start_scenario("smoke/greeting_01", "client-1")
    assert run_id.startswith("eval_")
    assert manager.is_running("client-1")
    await asyncio.sleep(0.1)
    assert not manager.is_running("client-1")


@pytest.mark.asyncio
async def test_start_pushes_setup_progress_immediately() -> None:
    notifier = _notifier()
    manager = EvalJobManager(notifier=notifier)
    manager._execute_scenario = AsyncMock()  # type: ignore[method-assign]

    run_id = await manager.start_scenario("smoke/greeting_01", "client-1")
    await asyncio.sleep(0.05)

    first_call = notifier.send_to_client.await_args_list[0].args
    assert first_call[0] == "client-1"
    payload = first_call[1]
    assert payload["type"] == "eval_progress"
    assert payload["run_id"] == run_id
    assert payload["phase"] == "setup"


@pytest.mark.asyncio
async def test_duplicate_start_raises_conflict() -> None:
    notifier = _notifier()
    manager = EvalJobManager(notifier=notifier)
    manager._client_active["client-1"] = "eval_existing"

    with pytest.raises(EvalJobConflictError):
        await manager.start_scenario("smoke/greeting_01", "client-1")


@pytest.mark.asyncio
async def test_cancel_returns_false_for_unknown_run() -> None:
    manager = EvalJobManager(notifier=_notifier())
    assert await manager.cancel("eval_missing") is False


@pytest.mark.asyncio
async def test_execute_pushes_setup_before_runner() -> None:
    notifier = _notifier()
    manager = EvalJobManager(notifier=notifier)
    fake_client = MagicMock()

    with (
        patch("eval.application.job_manager.resolve_scenario_by_id") as resolve_mock,
        patch(
            "eval.application.job_manager.EvalAgentPool.acquire_client",
            new=AsyncMock(return_value=(fake_client, True)),
        ),
        patch("eval.application.job_manager.EvalRunner") as runner_cls,
    ):
        resolve_mock.return_value = MagicMock(
            id="greeting_01",
            description="问候",
            tier="smoke",
            judge=None,
            setup=MagicMock(rounds=1),
            user_driver=MagicMock(turns=[]),
            assertions=[],
        )
        runner_cls.return_value.run_scenario = AsyncMock(return_value=MagicMock())

        await manager._execute_scenario(
            "eval_test",
            "smoke/greeting_01",
            "client-1",
            asyncio.Event(),
        )

    phases = [
        call.args[1]["phase"]
        for call in notifier.send_to_client.await_args_list
        if call.args[1].get("type") == "eval_progress"
    ]
    assert phases[0] == "setup"
    assert "setup" in phases
