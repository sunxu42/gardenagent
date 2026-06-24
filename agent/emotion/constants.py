"""情绪子系统内置常量（不暴露为 .config.yaml 开关）。"""

from __future__ import annotations

EMOTION_ALPHA = 0.48
EMOTION_BETA = 0.01
EMOTION_TAU_SEC = 14400.0
EMOTION_REL_ALPHA = 0.65
EMOTION_REL_TAU_SEC = 28800.0
EMOTION_APPRAISAL_SNAPSHOT_MAX = 64
EMOTION_APPRAISAL_TEMPERATURE = 0.1
EMOTION_APPRAISAL_MAX_USER_CHARS = 2000
EMOTION_USER_KEY = "default"
EMOTION_SYNTHESIS_EMPATHY_GAIN = 0.75
EMOTION_SYNTHESIS_WEIGHT_FLOOR = 0.35

# 用户情绪展示用中性参考（无跨会话 VAD 状态机）
USER_AFFECT_NEUTRAL_V = 0.0
USER_AFFECT_NEUTRAL_A = 0.2
USER_AFFECT_NEUTRAL_D = 0.0

EMOTION_ALLOWED: frozenset[str] = frozenset({
    "happy", "sad", "angry", "fear", "hate", "surprised", "neutral",
})

# 关系阶段代表点（与 derive_stage 一致，供测试锁定）
RELATIONSHIP_STAGE_PRESETS: dict[str, tuple[float, float]] = {
    "stranger": (0.20, 0.20),
    "acquaintance": (0.45, 0.45),
    "familiar": (0.50, 0.65),
    "trusted": (0.75, 0.50),
    "bonded": (0.80, 0.80),
}
