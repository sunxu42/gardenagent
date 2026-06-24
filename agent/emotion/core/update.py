"""情绪状态更新：惯性靠拢目标 + 向基线衰减。"""

from __future__ import annotations

import math

from agent.emotion.core.vad import VAD


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def apply_appraisal(
    current: VAD,
    target: VAD,
    baseline: VAD,
    *,
    alpha: float,
    beta: float,
    weight: float = 1.0,
) -> VAD:
    """一次 appraisal：先按 alpha*weight 朝 target 靠拢（惯性），再按 beta 朝 baseline 回归。"""
    ta = max(0.0, min(1.0, alpha * weight))
    cur = VAD(
        _lerp(current.v, target.v, ta),
        _lerp(current.a, target.a, ta),
        _lerp(current.d, target.d, ta),
    )
    tb = max(0.0, min(1.0, beta))
    cur = VAD(
        _lerp(cur.v, baseline.v, tb),
        _lerp(cur.a, baseline.a, tb),
        _lerp(cur.d, baseline.d, tb),
    )
    return cur.clamp()


def decay_over_time(current: VAD, baseline: VAD, *, dt_sec: float, tau_sec: float) -> VAD:
    """按时间间隔向基线衰减：beta_gap = 1 - exp(-dt/tau)。"""
    if dt_sec <= 0 or tau_sec <= 0:
        return current.clamp()
    beta_gap = 1.0 - math.exp(-dt_sec / tau_sec)
    out = VAD(
        _lerp(current.v, baseline.v, beta_gap),
        _lerp(current.a, baseline.a, beta_gap),
        _lerp(current.d, baseline.d, beta_gap),
    )
    return out.clamp()
