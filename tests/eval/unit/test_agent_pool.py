from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval.application.agent_client import EvalAgentClient
from eval.application.agent_pool import EvalAgentPool


@pytest.mark.asyncio
async def test_acquire_client_reuses_agent_manager() -> None:
    await EvalAgentPool.reset()
    fake_manager = MagicMock()
    fake_manager.aclose = AsyncMock()

    with patch.object(
        EvalAgentClient,
        "create_agent_manager",
        new=AsyncMock(return_value=fake_manager),
    ) as create_mock:
        first, cold_first = await EvalAgentPool.acquire_client()
        second, cold_second = await EvalAgentPool.acquire_client()

    assert cold_first is True
    assert cold_second is False
    assert first is not second
    create_mock.assert_awaited_once()
    await EvalAgentPool.reset()


@pytest.mark.asyncio
async def test_reset_closes_pooled_manager() -> None:
    await EvalAgentPool.reset()
    fake_manager = MagicMock()
    fake_manager.aclose = AsyncMock()

    with patch.object(
        EvalAgentClient,
        "create_agent_manager",
        new=AsyncMock(return_value=fake_manager),
    ):
        await EvalAgentPool.acquire_client()
        await EvalAgentPool.reset()

    fake_manager.aclose.assert_awaited_once()
