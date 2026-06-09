"""情绪子系统内置常量（不暴露为 .config.yaml 开关）。"""

from __future__ import annotations

EMOTION_ALPHA = 0.3
EMOTION_BETA = 0.05
EMOTION_TAU_SEC = 3600.0
EMOTION_REL_ALPHA = 0.3
EMOTION_REL_TAU_SEC = 7200.0
EMOTION_APPRAISAL_SNAPSHOT_MAX = 64
EMOTION_USER_AFFECT_EMA_ALPHA = 0.35
EMOTION_APPRAISAL_TEMPERATURE = 0.1
EMOTION_APPRAISAL_MAX_USER_CHARS = 2000
EMOTION_USER_KEY = "default"

# 用户情绪展示用中性参考（无跨会话 VAD 状态机）
USER_AFFECT_NEUTRAL_V = 0.0
USER_AFFECT_NEUTRAL_A = 0.2
USER_AFFECT_NEUTRAL_D = 0.0

EMOTION_ALLOWED: frozenset[str] = frozenset({
    "happy", "sad", "angry", "fear", "hate", "surprised", "neutral",
})
