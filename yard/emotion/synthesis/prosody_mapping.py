"""TTS 韵律预设：策略标签 → 火山情感 + prosody 参数。"""

from __future__ import annotations

from dataclasses import dataclass

from yard.emotion.core.vad import VAD


@dataclass(frozen=True)
class ProsodyPreset:
    emotion: str
    emotion_scale: int
    speech_rate: int
    pitch: int
    loudness_rate: int = 0


_PROFILE_PRESETS: dict[str, ProsodyPreset] = {
    "calm_steady": ProsodyPreset("neutral", 3, -10, -2, -5),
    "warm_comfort": ProsodyPreset("happy", 3, -8, -3, 0),
    "cheerful_light": ProsodyPreset("happy", 4, 4, 2, 5),
    "neutral_warm": ProsodyPreset("neutral", 4, 0, 0, 0),
}


def map_prosody(tts_profile: str, vad_target: VAD) -> ProsodyPreset:
    """查表得基础 preset，再用 VAD 做小幅微调（±5）。"""
    base = _PROFILE_PRESETS.get(tts_profile) or _PROFILE_PRESETS["neutral_warm"]
    rate_adj = int(max(-5, min(5, round((vad_target.a - 0.35) * 12))))
    pitch_adj = int(max(-5, min(5, round(vad_target.v * 4 + (vad_target.a - 0.3) * 3))))
    return ProsodyPreset(
        emotion=base.emotion,
        emotion_scale=base.emotion_scale,
        speech_rate=max(-50, min(50, base.speech_rate + rate_adj)),
        pitch=max(-12, min(12, base.pitch + pitch_adj)),
        loudness_rate=max(-50, min(50, base.loudness_rate)),
    )
