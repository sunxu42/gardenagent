"""情绪子系统装配：构建 EmotionService 与 appraisal middleware。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent.emotion.constants import (
    EMOTION_ALLOWED,
    EMOTION_ALPHA,
    EMOTION_APPRAISAL_MAX_USER_CHARS,
    EMOTION_APPRAISAL_SNAPSHOT_MAX,
    EMOTION_BETA,
    EMOTION_REL_ALPHA,
    EMOTION_REL_TAU_SEC,
    EMOTION_TAU_SEC,
    EMOTION_USER_KEY,
)
from agent.emotion.core.relationship import RelationshipState
from agent.emotion.core.service import EmotionService
from agent.emotion.core.store import EmotionStore
from agent.emotion.core.vad import VAD
from agent.emotion.llm.appraisal import (
    EmotionAppraiser,
    create_emotion_appraisal_model,
)
from agent.middlewares.emotion_appraisal import EmotionAppraisalMiddleware
from agent.prompt.persona.soul_profile import resolve_soul_profile


@dataclass
class EmotionSubsystem:
    service: EmotionService | None = None
    tts_voice_type: str | None = None
    appraisal_middleware: list[Any] = field(default_factory=list)


def build_emotion_service(config, persona_id=None) -> tuple[EmotionService, str]:
    """据 soul.yaml（或默认）的 baseline/voice_type 构建 EmotionService。"""
    alpha = float(getattr(config, "emotion_alpha", EMOTION_ALPHA) or EMOTION_ALPHA)
    beta = float(getattr(config, "emotion_beta", EMOTION_BETA) or EMOTION_BETA)
    tau_sec = float(getattr(config, "emotion_tau_sec", EMOTION_TAU_SEC) or EMOTION_TAU_SEC)
    rel_alpha = float(getattr(config, "emotion_rel_alpha", EMOTION_REL_ALPHA) or EMOTION_REL_ALPHA)
    rel_tau_sec = float(
        getattr(config, "emotion_rel_tau_sec", EMOTION_REL_TAU_SEC) or EMOTION_REL_TAU_SEC
    )
    snapshot_max = int(
        getattr(config, "emotion_appraisal_snapshot_max", EMOTION_APPRAISAL_SNAPSHOT_MAX)
        or EMOTION_APPRAISAL_SNAPSHOT_MAX
    )
    user_key = str(getattr(config, "emotion_user_key", EMOTION_USER_KEY) or EMOTION_USER_KEY)
    allowed = getattr(config, "emotion_allowed", None)
    allowed_emotions = set(allowed) if allowed else set(EMOTION_ALLOWED)
    state_path = Path(getattr(config, "emotion_state_path", "") or "")
    if not str(state_path):
        state_path = Path(config.workspace_dir) / "emotion" / "emotion_state.json"
    prof = resolve_soul_profile(config.prompts_dir, persona_id)
    base = prof["baseline"]
    rel_base = prof.get("relationship_baseline") or {}
    relationship_baseline = RelationshipState(
        trust=float(rel_base.get("trust", 0.5)),
        warmth=float(rel_base.get("warmth", 0.4)),
        baseline_trust=float(rel_base.get("trust", 0.5)),
        baseline_warmth=float(rel_base.get("warmth", 0.4)),
    )
    service = EmotionService(
        key=user_key,
        baseline=VAD(base["v"], base["a"], base["d"]),
        store=EmotionStore(str(state_path)),
        allowed_emotions=allowed_emotions,
        alpha=alpha,
        beta=beta,
        tau_sec=tau_sec,
        rel_alpha=rel_alpha,
        rel_tau_sec=rel_tau_sec,
        relationship_baseline=relationship_baseline,
        appraisal_snapshot_max=snapshot_max,
    )
    return service, prof["voice_type"]


def setup_emotion_subsystem(config) -> EmotionSubsystem:
    """构建情绪服务与 appraisal middleware。"""
    if not getattr(config, "emotion_enabled", True):
        return EmotionSubsystem()
    try:
        emotion_service, voice_type = build_emotion_service(config)
        appraisal_middleware: list[Any] = []
        if getattr(config, "emotion_appraisal_enabled", True):
            appraisal_llm = create_emotion_appraisal_model(config)
            max_user_chars = int(
                getattr(config, "emotion_appraisal_max_user_chars", EMOTION_APPRAISAL_MAX_USER_CHARS)
                or EMOTION_APPRAISAL_MAX_USER_CHARS
            )
            appraiser = EmotionAppraiser(
                appraisal_llm,
                max_user_chars=max_user_chars,
            )
            appraisal_middleware = [
                EmotionAppraisalMiddleware(emotion_service, appraiser),
            ]

        return EmotionSubsystem(
            service=emotion_service,
            tts_voice_type=voice_type,
            appraisal_middleware=appraisal_middleware,
        )
    except Exception as e:
        print(f"[warn] emotion subsystem disabled: {e}")
        return EmotionSubsystem()
