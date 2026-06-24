import pytest

from eval.application.agent_client import EvalAgentClient


class _FakeAgentManager:
    async def achat(self, user_input: str, *, thread_id: str):
        yield {"content": "你好"}
        yield {"updates": ">> 调用工具: read_file"}

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_respond_with_observation_collects_updates() -> None:
    client = EvalAgentClient(_FakeAgentManager(), owns_manager=True)
    text, affect, updates, latency_ms = await client.respond_with_observation("hi", "t1")
    assert text == "你好"
    assert affect is None
    assert latency_ms is not None
    assert any("read_file" in item for item in updates)
