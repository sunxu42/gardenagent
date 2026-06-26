from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import uuid4

from eval.api.schemas import AgentAffectSnapshot
from eval.api.mapping import observation_to_turn
from eval.domain.assertions.engine import AssertionEngine
from eval.domain.judge.metrics_registry import load_metric_refs
from eval.domain.judge.policy import evaluate_policy
from eval.domain.judge.runner import JudgeRunner
from eval.domain.models import AssertionResult, EvalRunResult, JudgeMetricResult, ToolEvent, TurnObservation
from eval.domain.progress import EvalProgressEvent
from eval.infrastructure.recorder import RunRecorder
from eval.domain.scenario import ScenarioFixture
from eval.domain.users.scripted_user import ScriptedUser
from shared.config.paths import resolve_eval_runs_dir

ProgressCallback = Callable[[EvalProgressEvent], Awaitable[None] | None]


class AgentClientProtocol(Protocol):
    async def respond_with_observation(
        self,
        message: str,
        thread_id: str,
    ) -> tuple[str, AgentAffectSnapshot | None, tuple[str, ...], float]: ...

    async def aclose(self) -> None: ...


class EvalRunner:
    """Orchestrates scenario evaluation with L0 assertions."""

    def __init__(
        self,
        agent_client: AgentClientProtocol,
        assertion_engine: AssertionEngine | None = None,
        judge_runner: JudgeRunner | None = None,
    ) -> None:
        self._agent_client = agent_client
        self._assertion_engine = assertion_engine or AssertionEngine()
        self._judge_runner = judge_runner

    async def run_scenario(
        self,
        scenario: ScenarioFixture,
        *,
        persist: bool = False,
        persist_dir: str | Path | None = None,
        progress_callback: ProgressCallback | None = None,
        cancel_event: asyncio.Event | None = None,
        run_id: str | None = None,
        recorder: RunRecorder | None = None,
    ) -> EvalRunResult:
        """Run one scripted scenario and evaluate configured assertions."""

        from eval.infrastructure.persistence import persist_record_safe, save_run

        resolved_run_id = run_id or f"eval_{uuid4().hex[:12]}"
        thread_id = f"{resolved_run_id}_thread"
        observations: list[TurnObservation] = []
        assertions: tuple[AssertionResult, ...] = ()
        judge_results: tuple[JudgeMetricResult, ...] = ()

        if recorder is not None:
            recorder.mark_phase_start("agent")
            recorder.set_telemetry(totals={"rounds": scenario.setup.rounds or len(scenario.user_driver.turns)})

        await _emit(
            progress_callback,
            EvalProgressEvent(
                type="eval_started",
                run_id=resolved_run_id,
                payload={
                    "scenario_id": scenario.id,
                    "tier": scenario.tier,
                    "description": scenario.description,
                },
            ),
            recorder=recorder,
        )

        try:
            user = ScriptedUser(scenario.user_driver)
            rounds = scenario.setup.rounds or len(scenario.user_driver.turns)
            for round_index in range(1, rounds + 1):
                if _is_cancelled(cancel_event):
                    return await _finalize_cancelled(
                        resolved_run_id,
                        scenario,
                        observations,
                        assertions,
                        judge_results,
                        progress_callback,
                        persist,
                        persist_dir,
                        recorder=recorder,
                    )

                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_progress",
                        run_id=resolved_run_id,
                        payload={
                            "phase": "agent",
                            "message": f"第 {round_index}/{rounds} 轮：生成用户台词…",
                            "round": round_index,
                            "total_rounds": rounds,
                        },
                    ),
                    recorder=recorder,
                )

                user_text = await user.generate_turn(scenario, observations, round_index)
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_progress",
                        run_id=resolved_run_id,
                        payload={
                            "phase": "agent",
                            "message": f"第 {round_index}/{rounds} 轮：Agent 回复中…",
                            "round": round_index,
                            "total_rounds": rounds,
                            "user": user_text,
                        },
                    ),
                    recorder=recorder,
                )
                assistant_text, affect, updates, latency_ms = await self._agent_client.respond_with_observation(
                    user_text,
                    thread_id,
                )
                observation = TurnObservation(
                    round=round_index,
                    user_text=user_text,
                    assistant_text=assistant_text,
                    tool_events=_parse_tool_events(updates),
                    agent_affect=affect,
                    raw_updates=updates,
                    latency_ms=latency_ms,
                )
                observations.append(observation)

                turn = observation_to_turn(observation)
                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_turn",
                        run_id=resolved_run_id,
                        payload={
                            "round": turn.round,
                            "user": turn.user,
                            "assistant": turn.assistant,
                            "agent_affect": (
                                turn.agent_affect.model_dump(mode="json")
                                if turn.agent_affect is not None
                                else None
                            ),
                        },
                    ),
                    recorder=recorder,
                )

                if (
                    scenario.setup.session_reset_after_round is not None
                    and round_index == scenario.setup.session_reset_after_round
                ):
                    thread_id = f"{resolved_run_id}_thread_reset_{round_index}"

            if _is_cancelled(cancel_event):
                return await _finalize_cancelled(
                    resolved_run_id,
                    scenario,
                    observations,
                    assertions,
                    judge_results,
                    progress_callback,
                    persist,
                    persist_dir,
                    recorder=recorder,
                )

            if recorder is not None:
                recorder.mark_phase_end("agent")
                recorder.mark_phase_start("assertions")

            assertions = self._assertion_engine.evaluate(observations, scenario.assertions)
            assertion_passed = all(
                item.status.value in {"pass", "warn", "skip"} for item in assertions
            )
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_progress",
                    run_id=resolved_run_id,
                    payload={
                        "phase": "assertions",
                        "message": "正在执行 L0 断言…",
                    },
                ),
                recorder=recorder,
            )
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_assertions",
                    run_id=resolved_run_id,
                    payload={
                        "assertions": [
                            {
                                "name": item.name,
                                "status": item.status.value,
                                "message": item.message,
                            }
                            for item in assertions
                        ],
                    },
                ),
                recorder=recorder,
            )

            judge_overall_passed: bool | None = None
            if (
                scenario.judge is not None
                and scenario.judge.enabled
                and self._judge_runner is not None
            ):
                if _is_cancelled(cancel_event):
                    return await _finalize_cancelled(
                        resolved_run_id,
                        scenario,
                        observations,
                        assertions,
                        judge_results,
                        progress_callback,
                        persist,
                        persist_dir,
                        recorder=recorder,
                    )

                if recorder is not None:
                    recorder.mark_phase_end("assertions")
                    recorder.mark_phase_start("judge")

                metric_definitions = load_metric_refs(scenario.judge.metrics)
                total_metrics = len(metric_definitions)
                if recorder is not None:
                    recorder.set_telemetry(totals={"rounds": rounds, "judge_metrics": total_metrics})

                await _emit(
                    progress_callback,
                    EvalProgressEvent(
                        type="eval_progress",
                        run_id=resolved_run_id,
                        payload={
                            "phase": "judge",
                            "message": f"Judge 评分 0/{total_metrics}",
                            "judge_index": 0,
                            "judge_total": total_metrics,
                        },
                    ),
                    recorder=recorder,
                )

                completed_metrics = 0

                async def _on_metric_done(metric_result: JudgeMetricResult) -> None:
                    nonlocal completed_metrics
                    completed_metrics += 1
                    await _emit(
                        progress_callback,
                        EvalProgressEvent(
                            type="eval_judge_metric",
                            run_id=resolved_run_id,
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
                            run_id=resolved_run_id,
                            payload={
                                "phase": "judge",
                                "message": f"Judge 评分 {completed_metrics}/{total_metrics}：{metric_result.name}",
                                "judge_index": completed_metrics,
                                "judge_total": total_metrics,
                                "metric_name": metric_result.name,
                            },
                        ),
                        recorder=recorder,
                    )

                judge_results = await self._judge_runner.a_evaluate(
                    observations,
                    scenario.judge,
                    metric_definitions,
                    scenario_description=scenario.description or scenario.id,
                    on_metric_done=_on_metric_done,
                    cancel_check=lambda: _is_cancelled(cancel_event),
                )
                if _is_cancelled(cancel_event):
                    return await _finalize_cancelled(
                        resolved_run_id,
                        scenario,
                        observations,
                        assertions,
                        judge_results,
                        progress_callback,
                        persist,
                        persist_dir,
                        recorder=recorder,
                    )
                judge_overall_passed = evaluate_policy(judge_results, scenario.judge.policy)
                if recorder is not None:
                    recorder.mark_phase_end("judge")
            elif recorder is not None:
                recorder.mark_phase_end("assertions")

            status = "completed"
            if not assertion_passed:
                status = "failed"
            if judge_overall_passed is False:
                status = "failed"

            result = EvalRunResult(
                run_id=resolved_run_id,
                scenario_id=scenario.id,
                tier=scenario.tier,
                mode="scenario",
                status=status,
                observations=tuple(observations),
                assertions=assertions,
                judge_results=judge_results,
                judge_overall_passed=judge_overall_passed,
            )
            if persist:
                if recorder is not None:
                    persist_record_safe(
                        recorder.build(
                            status=status,
                            observations=tuple(observations),
                            assertions=assertions,
                            judge_results=judge_results,
                            judge_overall_passed=judge_overall_passed,
                        ),
                        base_dir=persist_dir,
                    )
                else:
                    save_run(result, base_dir=persist_dir)

            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_completed",
                    run_id=resolved_run_id,
                    payload={
                        "status": status,
                        "judge_overall_passed": judge_overall_passed,
                    },
                ),
                recorder=recorder,
            )
            return result
        except Exception as exc:
            result = EvalRunResult(
                run_id=resolved_run_id,
                scenario_id=scenario.id,
                tier=scenario.tier,
                mode="scenario",
                status="failed",
                observations=tuple(observations),
                assertions=assertions,
                judge_results=judge_results,
                error=str(exc),
            )
            if persist:
                if recorder is not None:
                    persist_record_safe(
                        recorder.build(
                            status="failed",
                            observations=tuple(observations),
                            assertions=assertions,
                            judge_results=judge_results,
                            error=str(exc),
                        ),
                        base_dir=persist_dir,
                    )
                else:
                    save_run(result, base_dir=persist_dir)
            await _emit(
                progress_callback,
                EvalProgressEvent(
                    type="eval_failed",
                    run_id=resolved_run_id,
                    payload={"error": {"code": "eval_run_failed", "message": str(exc)}},
                ),
                recorder=recorder,
            )
            return result
        finally:
            await self._agent_client.aclose()


def _is_cancelled(cancel_event: asyncio.Event | None) -> bool:
    return cancel_event is not None and cancel_event.is_set()


async def _finalize_cancelled(
    run_id: str,
    scenario: ScenarioFixture,
    observations: list[TurnObservation],
    assertions: tuple[AssertionResult, ...],
    judge_results: tuple[JudgeMetricResult, ...],
    progress_callback: ProgressCallback | None,
    persist: bool,
    persist_dir: str,
    *,
    recorder: RunRecorder | None = None,
) -> EvalRunResult:
    from eval.infrastructure.persistence import persist_record_safe, save_run

    result = EvalRunResult(
        run_id=run_id,
        scenario_id=scenario.id,
        tier=scenario.tier,
        mode="scenario",
        status="cancelled",
        observations=tuple(observations),
        assertions=assertions,
        judge_results=judge_results,
    )
    if persist:
        if recorder is not None:
            recorder.mark_phase_end("agent")
            persist_record_safe(
                recorder.build(
                    status="cancelled",
                    observations=tuple(observations),
                    assertions=assertions,
                    judge_results=judge_results,
                ),
                base_dir=persist_dir,
            )
        else:
            save_run(result, base_dir=persist_dir)
    await _emit(
        progress_callback,
        EvalProgressEvent(
            type="eval_cancelled",
            run_id=run_id,
            payload={"status": "cancelled"},
        ),
        recorder=recorder,
    )
    return result


async def _emit(
    callback: ProgressCallback | None,
    event: EvalProgressEvent,
    *,
    recorder: RunRecorder | None = None,
) -> None:
    if recorder is not None:
        recorder.record(event)
    if callback is None:
        return
    result = callback(event)
    if asyncio.iscoroutine(result):
        await result


def _parse_tool_events(updates: tuple[str, ...]) -> tuple[ToolEvent, ...]:
    events: list[ToolEvent] = []
    pattern = re.compile(r"调用工具:\s*(\S+)")
    for item in updates:
        match = pattern.search(item)
        if match:
            events.append(ToolEvent(name=match.group(1), detail=item))
    return tuple(events)
