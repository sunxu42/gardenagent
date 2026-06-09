"""3D VAD 情感模型：数据类、火山 7 情感原型、最近原型投影。"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


@dataclass
class VAD:
    v: float  # valence ∈ [-1, 1]
    a: float  # arousal ∈ [0, 1]
    d: float  # dominance ∈ [-1, 1]

    def clamp(self) -> "VAD":
        return VAD(_clamp(self.v, -1.0, 1.0), _clamp(self.a, 0.0, 1.0), _clamp(self.d, -1.0, 1.0))

    def as_dict(self) -> dict:
        return {"v": self.v, "a": self.a, "d": self.d}

    @staticmethod
    def from_dict(data: dict) -> "VAD":
        return VAD(float(data["v"]), float(data["a"]), float(data["d"])).clamp()


# 火山 7 情感（参数串）原型坐标
EMOTION_PROTOTYPES: dict[str, VAD] = {
    "happy": VAD(0.8, 0.7, 0.5),
    "surprised": VAD(0.1, 0.8, -0.1),
    "neutral": VAD(0.0, 0.3, 0.0),
    "sad": VAD(-0.7, 0.3, -0.5),
    "fear": VAD(-0.6, 0.8, -0.7),
    "angry": VAD(-0.6, 0.8, 0.6),
    "hate": VAD(-0.7, 0.5, 0.2),
}

ALL_EMOTIONS: frozenset[str] = frozenset(EMOTION_PROTOTYPES)


def _dist(a: VAD, b: VAD) -> float:
    return math.sqrt((a.v - b.v) ** 2 + (a.a - b.a) ** 2 + (a.d - b.d) ** 2)


def _emotion_scale(vad: VAD) -> int:
    # 强度 = 效价绝对值与唤醒的均值，映射到 1..5
    intensity = min(1.0, (abs(vad.v) + vad.a) / 2.0)
    return max(1, min(5, round(1 + intensity * 4)))


def project(vad: VAD, allowed: "set[str] | frozenset[str]") -> tuple[str, int]:
    """VAD → (火山 emotion, emotion_scale)。仅在 allowed 白名单内取最近原型。"""
    candidates = [e for e in allowed if e in EMOTION_PROTOTYPES]
    if not candidates:
        return "neutral", 4
    label = min(candidates, key=lambda e: _dist(vad, EMOTION_PROTOTYPES[e]))
    return label, _emotion_scale(vad)
