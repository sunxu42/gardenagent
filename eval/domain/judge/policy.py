from __future__ import annotations

from collections.abc import Sequence

from eval.domain.models import JudgeMetricResult
from eval.domain.scenario import JudgePolicyConfig


def evaluate_policy(
    results: Sequence[JudgeMetricResult],
    policy: JudgePolicyConfig,
) -> bool:
    """Return whether judge metrics satisfy the configured policy."""

    if not results:
        return False

    blocking = set(policy.blocking)
    for item in results:
        if item.blocking or item.name in blocking:
            if not item.passed:
                return False

    overall = sum(item.score for item in results) / len(results)
    return overall >= policy.min_overall
