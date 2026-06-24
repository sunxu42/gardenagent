from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from shared.config.paths import resolve_eval_metrics_dir

METRICS_ROOT = resolve_eval_metrics_dir()

JUDGE_REASON_LANGUAGE_RULE = (
    "输出要求：你必须使用简体中文撰写评分理由（reason）；"
    "分数解释、扣分依据与总结均不得使用英文或其他语言。"
)

JUDGE_REASON_LANGUAGE_STEP = "最后用简体中文撰写评分理由，说明给分或扣分的具体依据。"


def augment_judge_criteria(criteria: str) -> str:
    """Append Chinese-output requirement to judge metric criteria."""

    text = criteria.strip()
    if "简体中文" in text and "评分理由" in text:
        return text
    return f"{text}\n\n{JUDGE_REASON_LANGUAGE_RULE}"


def augment_judge_evaluation_steps(steps: tuple[str, ...]) -> tuple[str, ...]:
    """Append Chinese-output step to judge evaluation_steps."""

    if any("简体中文" in step for step in steps):
        return steps
    return (*steps, JUDGE_REASON_LANGUAGE_STEP)


@dataclass(frozen=True)
class MetricDefinition:
    ref: str
    name: str
    criteria: str
    threshold: float
    blocking: bool = False
    evaluation_steps: tuple[str, ...] = ()


def load_metric_ref(ref: str) -> MetricDefinition:
    """Load one metric definition by group.name reference."""

    group, name = ref.split(".", maxsplit=1)
    payload = yaml.safe_load((METRICS_ROOT / f"{group}.yaml").read_text(encoding="utf-8"))
    raw = payload["metrics"][name]
    steps = raw.get("evaluation_steps") or []
    return MetricDefinition(
        ref=ref,
        name=name,
        criteria=raw["criteria"].strip(),
        threshold=float(raw["threshold"]),
        blocking=bool(raw.get("blocking", False)),
        evaluation_steps=tuple(str(step).strip() for step in steps if str(step).strip()),
    )


def load_metric_refs(refs: list[str]) -> tuple[MetricDefinition, ...]:
    """Load multiple metric definitions preserving order."""

    return tuple(load_metric_ref(ref) for ref in refs)


def build_conversational_geval(definition: MetricDefinition, model: object):
    """Create a ConversationalGEval metric from a registry definition."""

    from deepeval.metrics import ConversationalGEval
    from deepeval.test_case import MultiTurnParams

    kwargs: dict[str, object] = {
        "name": definition.name,
        "criteria": augment_judge_criteria(definition.criteria),
        "threshold": definition.threshold,
        "model": model,
        "evaluation_params": [MultiTurnParams.ROLE, MultiTurnParams.CONTENT],
        "async_mode": False,
    }
    steps = augment_judge_evaluation_steps(definition.evaluation_steps)
    if steps:
        kwargs["evaluation_steps"] = list(steps)
    return ConversationalGEval(**kwargs)
