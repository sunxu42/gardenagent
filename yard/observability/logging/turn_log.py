"""对话轮次结构化日志辅助（终端 + UI 同源）。"""

from __future__ import annotations

from typing import Any, Mapping

from yard.observability.logging import LogModule, get_logger
from yard.observability.logging.formatting import format_sec


def _quote_text(text: str) -> str:
    """日志行内引用用户/助手原文（换行压成空格）。"""
    collapsed = " ".join((text or "").split())
    return f'"{collapsed}"'


def format_vad(vad: Mapping[str, Any] | None) -> str:
    if not isinstance(vad, dict):
        return "—"
    v = vad.get("v")
    a = vad.get("a")
    d = vad.get("d")
    if not all(isinstance(x, (int, float)) for x in (v, a, d)):
        return "—"
    return f"v={v:.2f} a={a:.2f} d={d:.2f}"


def format_policy(policy: Mapping[str, Any] | None) -> str:
    if not isinstance(policy, dict):
        return "—"
    empathy = policy.get("empathy_mode", "—")
    stance = policy.get("stance", "—")
    repair = policy.get("repair_action", "none")
    direct = policy.get("directiveness")
    direct_s = f"{float(direct):.1f}" if isinstance(direct, (int, float)) else "—"
    return f"empathy={empathy} stance={stance} repair={repair} direct={direct_s}"


def log_user_to_agent(*, text: str, source: str, asr_sec: float | None = None) -> None:
    quoted = _quote_text(text)
    asr_part = f" · ASR {format_sec(asr_sec)}" if asr_sec is not None and asr_sec > 0 else ""
    get_logger(LogModule.HANDLER).info(
        f"user → agent{asr_part} · {quoted}",
        event="user_sent",
        user_text=text,
        source=source,
        asr_sec=round(asr_sec, 3) if asr_sec and asr_sec > 0 else None,
    )


def log_emotion_appraisal_start(*, cached: bool = False) -> None:
    msg = "emotion appraisal · cached snapshot" if cached else "emotion appraisal · start"
    get_logger(LogModule.EMOTION).info(msg, event="emotion_start", cached=cached)


def log_emotion_appraisal_done(
    *,
    duration_sec: float,
    metrics: Mapping[str, Any],
    cached: bool = False,
) -> None:
    user_vad = metrics.get("user_affect_vad") or metrics.get("utterance_vad")
    agent_target = metrics.get("agent_vad_target")
    policy = metrics.get("response_policy")
    rel = metrics.get("relationship") if isinstance(metrics.get("relationship"), dict) else {}
    cue = metrics.get("interpersonal_cue") or ""
    agent_emotion = metrics.get("agent_emotion", "")
    duration_label = format_sec(duration_sec) if not cached else "0.00s"
    prefix = "emotion appraisal · done (cached)" if cached else f"emotion appraisal · done · {duration_label}"
    message = (
        f"{prefix} | user {format_vad(user_vad)} | "
        f"agent target {format_vad(agent_target)} | {format_policy(policy)}"
    )
    if isinstance(cue, str) and cue.strip():
        message += f" | cue: {cue.strip()[:40]}"
    get_logger(LogModule.EMOTION).info(
        message,
        event="emotion_done",
        duration_sec=round(duration_sec, 3),
        cached=cached,
        user_affect_vad=dict(user_vad) if isinstance(user_vad, dict) else None,
        agent_vad_target=dict(agent_target) if isinstance(agent_target, dict) else None,
        response_policy=dict(policy) if isinstance(policy, dict) else None,
        relationship=dict(rel) if rel else None,
        interpersonal_cue=cue if isinstance(cue, str) else None,
        agent_emotion=agent_emotion or None,
    )


def log_emotion_settled(*, metrics: Mapping[str, Any]) -> None:
    after = metrics.get("agent_vad_after")
    emotion = metrics.get("agent_emotion", "neutral")
    scale = metrics.get("emotion_scale", 4)
    get_logger(LogModule.EMOTION).info(
        f"emotion settled | agent {format_vad(after)} · {emotion} (scale {scale})",
        event="emotion_settled",
        agent_vad_after=dict(after) if isinstance(after, dict) else None,
        agent_emotion=emotion,
        emotion_scale=scale,
    )


def log_agent_response_complete(*, text: str) -> None:
    quoted = _quote_text(text)
    get_logger(LogModule.AGENT).info(
        f"agent → user · {quoted}",
        event="agent_complete",
        assistant_text=text,
    )


def log_llm_ttft(seconds: float) -> None:
    get_logger(LogModule.AGENT).info(
        f"LLM TTFT {format_sec(seconds)}",
        event="llm_ttft",
        duration_sec=round(seconds, 3),
    )


def log_tts_first_chunk(seconds: float) -> None:
    get_logger(LogModule.TTS).info(
        f"TTS first chunk {format_sec(seconds)}",
        event="tts_first_chunk",
        duration_sec=round(seconds, 3),
    )


def log_memory_event(message: str, **extra: Any) -> None:
    get_logger(LogModule.MEMORY).info(message, event="memory", **extra)
