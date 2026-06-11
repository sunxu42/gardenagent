from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pytest
from langchain_core.messages import BaseMessage

from src.eval_api.schemas import EmotionEvalRequest, EmotionTurnResult
from src.evaluation.simulated_user import SimulatedUser, _history_prompt


def _request() -> EmotionEvalRequest:
    return EmotionEvalRequest(
        background="刚搬到新城市，感觉很孤单。",
        initial_mood="lonely",
        goal="测试助理是否能提供温暖支持",
    )


def test_history_prompt_describes_first_turn() -> None:
    prompt = _history_prompt([])

    assert "第一轮" in prompt
    assert "先自然地说出当前困扰" in prompt


def test_history_prompt_includes_prior_user_and_assistant_turns() -> None:
    turn = EmotionTurnResult(round=1, user="我有点难过", assistant="我在这里陪你")

    prompt = _history_prompt([turn])

    assert "用户：我有点难过" in prompt
    assert "助手：我在这里陪你" in prompt
    assert "继续以用户身份自然回应" in prompt


@dataclass(slots=True)
class FakeResponse:
    content: str


class FakeLlm:
    def __init__(self) -> None:
        self.messages: Sequence[BaseMessage] | None = None

    async def ainvoke(self, messages: Sequence[BaseMessage]) -> FakeResponse:
        self.messages = messages
        return FakeResponse(content="  hello  ")


@pytest.mark.asyncio
async def test_generate_turn_returns_stripped_llm_content() -> None:
    llm = FakeLlm()
    simulated_user = SimulatedUser(llm)

    result = await simulated_user.generate_turn(_request(), [], 1)

    assert result == "hello"
    assert llm.messages is not None
    assert len(llm.messages) == 2
