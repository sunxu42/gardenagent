from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from eval.api.schemas import EmotionEvalRequest, EmotionTurnResult
from shared.config.agent import Config


class _LlmResponse(Protocol):
    content: object


class _SimulatedUserLlm(Protocol):
    async def ainvoke(self, messages: Sequence[BaseMessage]) -> _LlmResponse:
        """Generate a simulated user response from chat messages."""


class SimulatedUser:
    """Generates natural user utterances for emotion-support evaluation."""

    def __init__(self, llm: _SimulatedUserLlm) -> None:
        """Initialize the simulated user with an async chat model."""

        self._llm = llm

    @classmethod
    def from_config(cls, config: Config) -> SimulatedUser:
        """Create a simulated user from application LLM configuration."""

        llm = ChatOpenAI(
            model=config.llm_model_name,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0.7,
        )
        return cls(llm)

    async def generate_turn(
        self,
        request: EmotionEvalRequest,
        history: Sequence[EmotionTurnResult],
        round_index: int,
    ) -> str:
        """Return one natural simulated user utterance for the current round."""

        response = await self._llm.ainvoke(
            [
                SystemMessage(content=_system_prompt(request, round_index)),
                HumanMessage(content=_history_prompt(history)),
            ],
        )
        content = response.content
        return (content if isinstance(content, str) else str(content)).strip()


def _system_prompt(request: EmotionEvalRequest, round_index: int) -> str:
    """Build the system prompt that fixes the simulated user's persona."""

    return (
        "你正在扮演一个用于情绪支持评估的真实用户。"
        "请始终保持同一个用户人格、背景和情绪状态推进，不要扮演助手。"
        "输出只能是一句自然的用户发言，不要解释、不要标注轮次、不要给出分析。\n\n"
        f"用户背景：{request.background}\n"
        f"初始情绪：{request.initial_mood}\n"
        f"本次目标：{request.goal}\n"
        f"当前轮次：第 {round_index} 轮，共 {request.rounds} 轮"
    )


def _history_prompt(history: Sequence[EmotionTurnResult]) -> str:
    """Build the user prompt from previous evaluation turns."""

    if not history:
        return "这是第一轮，请先自然地说出当前困扰，语气要符合背景和初始情绪。"

    lines = ["以下是此前对话，请延续同一个用户的感受和目标："]
    for turn in history:
        lines.append(f"用户：{turn.user}")
        lines.append(f"助手：{turn.assistant}")
    lines.append("请继续以用户身份自然回应助手，不要总结或评价测试。")
    return "\n".join(lines)
