from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

from src.eval_api.schemas import (
    AgentAffectSnapshot,
    EmotionEvalRequest,
    EmotionEvalResponse,
    EmotionTurnResult,
    EvalError,
)
from src.evaluation.emotion_metrics import EmotionEvaluation, EmotionSupportEvaluator

logger = logging.getLogger(__name__)


class SimulatedUserProtocol(Protocol):
    """Generates simulated user messages for each evaluation round."""

    async def generate_turn(
        self,
        request: EmotionEvalRequest,
        history: Sequence[EmotionTurnResult],
        round_index: int,
    ) -> str:
        """Return the simulated user message for the requested round."""


class AgentClientProtocol(Protocol):
    """Provides isolated assistant responses and lifecycle cleanup."""

    async def respond(
        self,
        message: str,
        thread_id: str,
    ) -> tuple[str, AgentAffectSnapshot | None]:
        """Return the assistant response and optional affect snapshot."""

    async def aclose(self) -> None:
        """Release client resources after an evaluation session."""


class EvaluatorProtocol(Protocol):
    """Scores completed emotion-support turns."""

    def evaluate(self, turns: Sequence[EmotionTurnResult]) -> EmotionEvaluation:
        """Return metric scores and summary for completed turns."""


class EvalSession:
    """Orchestrates one isolated emotion-support evaluation run."""

    def __init__(
        self,
        simulated_user: SimulatedUserProtocol,
        agent_client: AgentClientProtocol,
        evaluator: EvaluatorProtocol | None = None,
    ) -> None:
        """Initialize the session with injected dependencies."""

        self._simulated_user = simulated_user
        self._agent_client = agent_client
        self._evaluator = evaluator or EmotionSupportEvaluator()

    async def run(self, request: EmotionEvalRequest) -> EmotionEvalResponse:
        """Run the requested rounds and return a completed or failed response."""

        session_id = f"eval_{uuid4().hex[:12]}"
        thread_id = f"{session_id}_thread"
        turns: list[EmotionTurnResult] = []

        try:
            for round_index in range(1, request.rounds + 1):
                user_message = await self._simulated_user.generate_turn(
                    request,
                    turns,
                    round_index,
                )
                assistant_message, agent_affect = await self._agent_client.respond(
                    user_message,
                    thread_id,
                )
                turns.append(
                    EmotionTurnResult(
                        round=round_index,
                        user=user_message,
                        assistant=assistant_message,
                        agent_affect=agent_affect,
                    ),
                )

            evaluation = self._evaluator.evaluate(turns)
            return EmotionEvalResponse(
                session_id=session_id,
                status="completed",
                scenario=request,
                turns=turns,
                scores=evaluation.scores,
                summary=evaluation.summary,
            )
        except Exception as exc:
            return EmotionEvalResponse(
                session_id=session_id,
                status="failed",
                scenario=request,
                turns=turns,
                error=EvalError(
                    code="eval_session_failed",
                    message=str(exc),
                ),
            )
        finally:
            try:
                await self._agent_client.aclose()
            except Exception:
                logger.exception("failed to close eval agent client")
