from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EvalProgressType = Literal[
    "eval_started",
    "eval_progress",
    "eval_turn",
    "eval_assertions",
    "eval_judge_metric",
    "eval_completed",
    "eval_failed",
    "eval_cancelled",
]


@dataclass(frozen=True)
class EvalProgressEvent:
    """Internal progress event emitted during an eval run."""

    type: EvalProgressType
    run_id: str
    payload: dict[str, Any]
