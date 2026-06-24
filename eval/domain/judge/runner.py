from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Awaitable, Callable, Sequence

from eval.domain.judge.adapter import to_conversational_test_case
from eval.domain.judge.metrics_registry import MetricDefinition, build_conversational_geval
from eval.domain.models import JudgeMetricResult, TurnObservation
from eval.domain.scenario import JudgeConfig

_DEFAULT_METRIC_DELAY_SEC = 1.5

MetricDoneCallback = Callable[[JudgeMetricResult], Awaitable[None] | None]


def _metric_delay_sec() -> float:
    raw = os.getenv("EVAL_JUDGE_METRIC_DELAY_SEC", str(_DEFAULT_METRIC_DELAY_SEC))
    return max(0.0, float(raw))


class JudgeRunner:
    """Run DeepEval conversational judge metrics against observations."""

    def __init__(self, model: object) -> None:
        self._model = model

    async def a_evaluate(
        self,
        observations: Sequence[TurnObservation],
        judge_config: JudgeConfig,
        metric_definitions: Sequence[MetricDefinition],
        *,
        scenario_description: str | None = None,
        on_metric_done: MetricDoneCallback | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> tuple[JudgeMetricResult, ...]:
        """Score one conversation with configured judge metrics."""

        case = to_conversational_test_case(
            observations,
            scenario=scenario_description,
        )
        results: list[JudgeMetricResult] = []
        metric_delay = _metric_delay_sec()
        for index, definition in enumerate(metric_definitions):
            if cancel_check and cancel_check():
                break
            if index > 0 and metric_delay > 0:
                await asyncio.sleep(metric_delay)
                if cancel_check and cancel_check():
                    break
            metric = build_conversational_geval(definition, self._model)
            metric.measure(case, _show_indicator=False)
            score = float(metric.score or 0.0)
            passed = score >= definition.threshold
            metric_result = JudgeMetricResult(
                name=definition.name,
                score=score,
                passed=passed,
                threshold=definition.threshold,
                reason=metric.reason or "",
                blocking=definition.blocking,
            )
            results.append(metric_result)
            if on_metric_done is not None:
                callback_result = on_metric_done(metric_result)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
        return tuple(results)

    def evaluate(
        self,
        observations: Sequence[TurnObservation],
        judge_config: JudgeConfig,
        metric_definitions: Sequence[MetricDefinition],
        *,
        scenario_description: str | None = None,
        on_metric_done: MetricDoneCallback | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> tuple[JudgeMetricResult, ...]:
        """Synchronous judge evaluation for callers without a running event loop."""

        case = to_conversational_test_case(
            observations,
            scenario=scenario_description,
        )
        results: list[JudgeMetricResult] = []
        metric_delay = _metric_delay_sec()
        for index, definition in enumerate(metric_definitions):
            if cancel_check and cancel_check():
                break
            if index > 0 and metric_delay > 0:
                time.sleep(metric_delay)
                if cancel_check and cancel_check():
                    break
            metric = build_conversational_geval(definition, self._model)
            metric.measure(case, _show_indicator=False)
            score = float(metric.score or 0.0)
            passed = score >= definition.threshold
            metric_result = JudgeMetricResult(
                name=definition.name,
                score=score,
                passed=passed,
                threshold=definition.threshold,
                reason=metric.reason or "",
                blocking=definition.blocking,
            )
            results.append(metric_result)
            if on_metric_done is not None:
                on_metric_done(metric_result)
        return tuple(results)
