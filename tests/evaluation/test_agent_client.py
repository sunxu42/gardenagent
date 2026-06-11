from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from src.evaluation.agent_client import YardAgentClient


class FakeYardManager:
    def __init__(self) -> None:
        self.closed = False
        self.seen_message: str | None = None
        self.seen_thread_id: str | None = None

    async def achat(self, user_input: str, *, thread_id: str) -> AsyncIterator[dict[str, object]]:
        self.seen_message = user_input
        self.seen_thread_id = thread_id
        yield {"content": "a"}
        yield {"updates": "x"}
        yield {"content": "b"}

    def current_tts_emotion(self) -> tuple[str, float]:
        return ("calm", 0.8)

    def current_vad_metrics(self) -> dict[str, object]:
        return {"agent_vad_after": {"v": 0.3, "a": 0.2, "d": 0.5}}

    def current_relationship_snapshot(self) -> dict[str, object]:
        return {"stage": "trusted"}

    async def aclose(self) -> None:
        self.closed = True


class FailingAffectYardManager(FakeYardManager):
    def current_tts_emotion(self) -> tuple[str, float]:
        raise RuntimeError("emotion unavailable")

    def current_vad_metrics(self) -> dict[str, object]:
        raise RuntimeError("vad unavailable")

    def current_relationship_snapshot(self) -> dict[str, object]:
        raise RuntimeError("relationship unavailable")


@pytest.mark.asyncio
async def test_respond_collects_content_and_affect_snapshot() -> None:
    manager = FakeYardManager()
    client = YardAgentClient(manager)

    assistant_text, snapshot = await client.respond("hi", "thread-1")

    assert assistant_text == "ab"
    assert manager.seen_message == "hi"
    assert manager.seen_thread_id == "thread-1"
    assert snapshot is not None
    assert snapshot.emotion == "calm"
    assert snapshot.vad == {"v": 0.3, "a": 0.2, "d": 0.5}
    assert snapshot.relationship_stage == "trusted"


@pytest.mark.asyncio
async def test_respond_ignores_affect_helper_failures() -> None:
    manager = FailingAffectYardManager()
    client = YardAgentClient(manager)

    assistant_text, snapshot = await client.respond("hi", "thread-1")

    assert assistant_text == "ab"
    assert snapshot is None


@pytest.mark.asyncio
async def test_aclose_delegates_to_yard_manager() -> None:
    manager = FakeYardManager()
    client = YardAgentClient(manager)

    await client.aclose()

    assert manager.closed is True
