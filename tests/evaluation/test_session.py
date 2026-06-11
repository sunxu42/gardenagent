from __future__ import annotations

import asyncio
from collections.abc import Sequence

from src.eval_api.schemas import (
    EmotionEvalRequest,
    EmotionEvalResponse,
    EmotionMetricScore,
    EmotionTurnResult,
    EvalSummary,
)
from src.evaluation.emotion_metrics import EmotionEvaluation
from src.evaluation.session import EvalSession


class FakeSimulatedUser:
    async def generate_turn(
        self,
        request: EmotionEvalRequest,
        history: Sequence[EmotionTurnResult],
        round_index: int,
    ) -> str:
        return f"用户第 {round_index} 轮"


class FailingSimulatedUser:
    async def generate_turn(
        self,
        request: EmotionEvalRequest,
        history: Sequence[EmotionTurnResult],
        round_index: int,
    ) -> str:
        raise RuntimeError("simulated user unavailable")


class FakeAgentClient:
    def __init__(self, *, fail_on_close: bool = False) -> None:
        self.closed = False
        self.fail_on_close = fail_on_close

    async def respond(self, message: str, thread_id: str) -> tuple[str, None]:
        return f"助手回复：{message}", None

    async def aclose(self) -> None:
        self.closed = True
        if self.fail_on_close:
            raise RuntimeError("close unavailable")


class FailingAgentClient:
    def __init__(self, *, fail_on_close: bool = False) -> None:
        self.closed = False
        self.fail_on_close = fail_on_close

    async def respond(self, message: str, thread_id: str) -> tuple[str, None]:
        raise RuntimeError("agent unavailable")

    async def aclose(self) -> None:
        self.closed = True
        if self.fail_on_close:
            raise RuntimeError("close unavailable")


class FailingEvaluator:
    def evaluate(self, turns: Sequence[EmotionTurnResult]) -> EmotionEvaluation:
        raise RuntimeError("evaluator unavailable")


class FakeEvaluator:
    def evaluate(self, turns: Sequence[EmotionTurnResult]) -> EmotionEvaluation:
        return EmotionEvaluation(
            scores=[
                EmotionMetricScore(name="empathy", score=0.8, reason="ok"),
                EmotionMetricScore(name="boundary_safety", score=0.8, reason="ok"),
            ],
            summary=EvalSummary(
                overall_score=0.8,
                verdict="pass",
                conclusion="ok",
                improvement_suggestions=[],
            ),
        )


def test_eval_session_runs_requested_rounds() -> None:
    response = asyncio.run(_run_session())

    assert response.status == "completed"
    assert response.scenario is not None
    assert len(response.turns) == 3
    assert response.turns[0].user == "用户第 1 轮"
    assert response.summary is not None
    assert response.summary.verdict == "pass"


def test_eval_session_closes_agent_client_on_failure() -> None:
    agent_client = FailingAgentClient()
    response = asyncio.run(_run_failed_session(agent_client))

    assert response.status == "failed"
    assert response.error is not None
    assert response.error.code == "eval_session_failed"
    assert agent_client.closed is True


def test_eval_session_preserves_simulated_user_error_when_close_fails() -> None:
    agent_client = FakeAgentClient(fail_on_close=True)
    response = asyncio.run(
        _run_session_with_dependencies(
            simulated_user=FailingSimulatedUser(),
            agent_client=agent_client,
            evaluator=FakeEvaluator(),
        ),
    )

    assert response.status == "failed"
    assert response.error is not None
    assert response.error.message == "simulated user unavailable"
    assert agent_client.closed is True


def test_eval_session_preserves_evaluator_error_and_partial_turns_when_close_fails() -> None:
    agent_client = FakeAgentClient(fail_on_close=True)
    response = asyncio.run(
        _run_session_with_dependencies(
            simulated_user=FakeSimulatedUser(),
            agent_client=agent_client,
            evaluator=FailingEvaluator(),
        ),
    )

    assert response.status == "failed"
    assert response.error is not None
    assert response.error.message == "evaluator unavailable"
    assert len(response.turns) == 3
    assert agent_client.closed is True


def test_eval_session_preserves_agent_error_when_close_fails() -> None:
    agent_client = FailingAgentClient(fail_on_close=True)
    response = asyncio.run(_run_failed_session(agent_client))

    assert response.status == "failed"
    assert response.error is not None
    assert response.error.message == "agent unavailable"
    assert agent_client.closed is True


async def _run_session() -> EmotionEvalResponse:
    request = EmotionEvalRequest(
        background="独居，压力大",
        initial_mood="anxious",
        rounds=3,
    )
    session = EvalSession(
        simulated_user=FakeSimulatedUser(),
        agent_client=FakeAgentClient(),
        evaluator=FakeEvaluator(),
    )

    return await session.run(request)


async def _run_failed_session(
    agent_client: FailingAgentClient,
) -> EmotionEvalResponse:
    return await _run_session_with_dependencies(
        simulated_user=FakeSimulatedUser(),
        agent_client=agent_client,
        evaluator=FakeEvaluator(),
    )


async def _run_session_with_dependencies(
    simulated_user: FakeSimulatedUser | FailingSimulatedUser,
    agent_client: FakeAgentClient | FailingAgentClient,
    evaluator: FakeEvaluator | FailingEvaluator,
) -> EmotionEvalResponse:
    request = EmotionEvalRequest(
        background="独居，压力大",
        initial_mood="anxious",
        rounds=3,
    )
    session = EvalSession(
        simulated_user=simulated_user,
        agent_client=agent_client,
        evaluator=evaluator,
    )

    return await session.run(request)
