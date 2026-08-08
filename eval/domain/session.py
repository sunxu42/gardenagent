from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Protocol
from uuid import uuid4

from eval.api.schemas import (
    AgentAffectSnapshot,
    EmotionEvalRequest,
    EmotionEvalResponse,
    EmotionMetricScore,
    EmotionTurnResult,
    EvalError,
)
from eval.domain.emotion_metrics import EmotionEvaluation, EmotionSupportEvaluator
from eval.domain.models import JudgeMetricResult, TurnObservation
from eval.domain.progress import EvalProgressEvent
from eval.infrastructure.record import EvalRunRecord
from eval.infrastructure.recorder import RunRecorder
from eval.domain.runner import _emit
from shared.observability.logging import LogModule, get_logger

logger = get_logger(LogModule.EVAL)

ProgressCallback = Callable[[EvalProgressEvent], Awaitable[None] | None]


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

    async def a_evaluate(
        self,
        turns: Sequence[EmotionTurnResult],
        *,
        on_metric_done: Callable[..., Awaitable[None] | None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> EmotionEvaluation:
        """Return metric scores and summary for completed turns."""


async def _agent_turn(
    agent_client: AgentClientProtocol,
    message: str,
    thread_id: str,
) -> tuple[str, AgentAffectSnapshot | None, tuple[str, ...], float | None]:
    """Invoke the agent client and return latency when available."""

    respond_with_observation = getattr(agent_client, "respond_with_observation", None)
    if callable(respond_with_observation):
        text, affect, updates, latency_ms = await respond_with_observation(message, thread_id)
        return text, affect, updates, latency_ms
    text, affect = await agent_client.respond(message, thread_id)
    return text, affect, (), None


def _turns_to_observations(turns: Sequence[EmotionTurnResult]) -> tuple[TurnObservation, ...]:
    return tuple(
        TurnObservation(
            round=item.round,
            user_text=item.user,
            assistant_text=item.assistant,
            agent_affect=item.agent_affect,
        )
        for item in turns
    )


def _scores_to_judge_results(scores: Sequence[EmotionMetricScore]) -> tuple[JudgeMetricResult, ...]:
    return tuple(
        JudgeMetricResult(
            name=item.name,
            score=item.score,
            passed=item.score >= 0.7,
            threshold=0.7,
            reason=item.reason,
        )
        for item in scores
    )


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
        self._last_observations: tuple[TurnObservation, ...] = ()

    @property
    def last_observations(self) -> tuple[TurnObservation, ...]:
        """Observations collected during the most recent run."""

        return self._last_observations

    async def run(
        self,
        request: EmotionEvalRequest,
        *,
        run_id: str | None = None,
        progress_callback: ProgressCallback | None = None,
        cancel_event: asyncio.Event | None = None,
        recorder: RunRecorder | None = None,
    ) -> EmotionEvalResponse:
        """Run the requested rounds and return a completed or failed response."""

        session_id = run_id or f"eval_{uuid4().hex[:12]}"
        thread_id = f"{session_id}_thread"
        turns: list[EmotionTurnResult] = []
        observations: list[TurnObservation] = []
        label = f"情绪探索 · {request.initial_mood}"

        def _is_cancelled() -> bool:
            return cancel_event is not None and cancel_event.is_set()

        if recorder is not None:
            recorder.mark_phase_start("agent")
            recorder.set_telemetry(totals={"rounds": request.rounds})

        try:
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_started",
                    run_id=session_id,
                    payload={
                        "scenario_id": "exploratory",
                        "tier": "exploratory",
                        "description": label,
                    },
                ),
                recorder=recorder,
            )

            for round_index in range(1, request.rounds + 1):
                if _is_cancelled():
                    await _emit(
                        progress_callback,
                        EvalProgressEvent(
                            type="eval_cancelled",
                            run_id=session_id,
                            payload={},
                        ),
                        recorder=recorder,
                    )
                    return EmotionEvalResponse(
                        session_id=session_id,
                        status="cancelled",
                        scenario=request,
                        turns=turns,
                    )

                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_progress",
                        run_id=session_id,
                        payload={
                            "phase": "agent",
                            "message": f"第 {round_index}/{request.rounds} 轮对话进行中…",
                            "round": round_index - 1,
                            "total_rounds": request.rounds,
                        },
                    ),
                    recorder=recorder,
                )
                user_message = await self._simulated_user.generate_turn(
                    request,
                    turns,
                    round_index,
                )
                assistant_message, agent_affect, updates, latency_ms = await _agent_turn(
                    self._agent_client,
                    user_message,
                    thread_id,
                )
                turn = EmotionTurnResult(
                    round=round_index,
                    user=user_message,
                    assistant=assistant_message,
                    agent_affect=agent_affect,
                )
                turns.append(turn)
                observations.append(
                    TurnObservation(
                        round=round_index,
                        user_text=user_message,
                        assistant_text=assistant_message,
                        agent_affect=agent_affect,
                        raw_updates=updates,
                        latency_ms=latency_ms,
                    )
                )
                if recorder is not None and latency_ms is not None:
                    recorder.set_telemetry(
                        totals={"rounds": request.rounds, f"latency_round_{round_index}": int(latency_ms)}
                    )
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_turn",
                        run_id=session_id,
                        payload={
                            "round": round_index,
                            "user": user_message,
                            "assistant": assistant_message,
                            "agent_affect": agent_affect.model_dump(mode="json")
                            if agent_affect is not None
                            else None,
                            "latency_ms": latency_ms,
                        },
                    ),
                    recorder=recorder,
                )

            if _is_cancelled():
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_cancelled",
                        run_id=session_id,
                        payload={},
                    ),
                    recorder=recorder,
                )
                return EmotionEvalResponse(
                    session_id=session_id,
                    status="cancelled",
                    scenario=request,
                    turns=turns,
                )

            if recorder is not None:
                recorder.mark_phase_end("agent")
                recorder.mark_phase_start("judge")

            from eval.domain.emotion_metrics import EXPLORATORY_METRIC_REFS
            from eval.domain.judge.metrics_registry import load_metric_refs

            metric_definitions = load_metric_refs(EXPLORATORY_METRIC_REFS)
            metric_count = len(metric_definitions)
            completed_metrics = 0
            if recorder is not None:
                recorder.set_telemetry(totals={"rounds": request.rounds, "judge_metrics": metric_count})

            async def _on_metric_done(metric_result: object) -> None:
                nonlocal completed_metrics
                if not isinstance(metric_result, JudgeMetricResult):
                    return
                completed_metrics += 1
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_judge_metric",
                        run_id=session_id,
                        payload={
                            "name": metric_result.name,
                            "score": metric_result.score,
                            "passed": metric_result.passed,
                            "threshold": metric_result.threshold,
                            "reason": metric_result.reason,
                        },
                    ),
                    recorder=recorder,
                )
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_progress",
                        run_id=session_id,
                        payload={
                            "phase": "judge",
                            "message": (
                                f"Judge 评分 {completed_metrics}/{metric_count}："
                                f"{metric_result.name}"
                            ),
                            "judge_index": completed_metrics,
                            "judge_total": metric_count,
                            "metric_name": metric_result.name,
                        },
                    ),
                    recorder=recorder,
                )

            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_progress",
                    run_id=session_id,
                    payload={
                        "phase": "judge",
                        "message": f"Judge 评分 0/{metric_count}",
                        "judge_index": 0,
                        "judge_total": metric_count,
                    },
                ),
                recorder=recorder,
            )

            evaluation = await self._evaluator.a_evaluate(
                turns,
                on_metric_done=_on_metric_done,
                cancel_check=_is_cancelled,
            )
            judge_overall_passed = evaluation.summary.verdict == "pass"
            if recorder is not None:
                recorder.mark_phase_end("judge")

            response = EmotionEvalResponse(
                session_id=session_id,
                status="completed",
                scenario=request,
                turns=turns,
                scores=evaluation.scores,
                summary=evaluation.summary,
            )
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_completed",
                    run_id=session_id,
                    payload={
                        "status": "completed",
                        "judge_overall_passed": judge_overall_passed,
                        "scores": [score.model_dump(mode="json") for score in evaluation.scores],
                        "summary": evaluation.summary.model_dump(mode="json")
                        if evaluation.summary is not None
                        else None,
                    },
                ),
                recorder=recorder,
            )
            return response
        except Exception as exc:
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_failed",
                    run_id=session_id,
                    payload={
                        "error": {
                            "code": "eval_session_failed",
                            "message": str(exc),
                        },
                    },
                ),
                recorder=recorder,
            )
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
            self._last_observations = tuple(observations)
            try:
                await self._agent_client.aclose()
            except Exception:
                logger.exception("failed to close eval agent client")


def build_exploratory_record(
    recorder: RunRecorder,
    response: EmotionEvalResponse,
    *,
    observations: tuple[TurnObservation, ...] | None = None,
    judge_overall_passed: bool | None = None,
) -> EvalRunRecord:
    """Build a persisted record from an exploratory session response."""

    resolved_observations = observations if observations is not None else _turns_to_observations(response.turns)
    scores = tuple(response.scores)
    return recorder.build(
        status=response.status,
        observations=resolved_observations,
        judge_results=_scores_to_judge_results(scores),
        judge_overall_passed=judge_overall_passed,
        exploratory_config=response.scenario,
        scores=scores,
        summary=response.summary,
        error=response.error.message if response.error is not None else None,
    )
