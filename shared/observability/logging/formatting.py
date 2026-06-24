"""日志展示格式化（时间单位统一为秒）。"""

from __future__ import annotations


def format_sec(seconds: float | None) -> str:
    """将秒格式化为日志用字符串，如 0.35s。"""
    if seconds is None:
        return "—"
    return f"{float(seconds):.2f}s"


def format_latency_summary(latency_s: dict[str, float | None]) -> str:
    """生成 METRICS 行人类可读摘要。"""
    parts: list[str] = []
    if latency_s.get("audio_e2e") is not None:
        parts.append(f"RTT {format_sec(latency_s['audio_e2e'])}")
    elif latency_s.get("text_e2e") is not None:
        parts.append(f"RTT {format_sec(latency_s['text_e2e'])}")
    segments: list[str] = []
    if latency_s.get("asr") is not None:
        segments.append(f"ASR {format_sec(latency_s['asr'])}")
    if latency_s.get("llm_ttft") is not None:
        segments.append(f"LLM {format_sec(latency_s['llm_ttft'])}")
    if latency_s.get("tts_first_chunk") is not None:
        segments.append(f"TTS {format_sec(latency_s['tts_first_chunk'])}")
    if segments:
        parts.append(" → ".join(segments))
    return " | ".join(parts) if parts else "metrics"
