from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TurnMetricsAggregator:
    audio_output: bool
    _turn_id: str | None = None
    _finalized: bool = False
    _sentence_ended: bool = False
    _latency: dict[str, float | None] = field(default_factory=lambda: {
        "asr": None,
        "llm_ttft": None,
        "tts_first_chunk": None,
        "text_e2e": None,
        "audio_e2e": None,
    })

    def begin_turn(self, turn_id: str) -> None:
        self._turn_id = turn_id
        self._finalized = False
        self._sentence_ended = False
        for k in self._latency:
            self._latency[k] = None

    def mark_asr(self, seconds: float) -> None:
        if seconds > 0:
            self._latency["asr"] = round(seconds, 3)

    def mark_llm_ttft(self, seconds: float) -> None:
        if seconds > 0:
            self._latency["llm_ttft"] = round(seconds, 3)
            self._latency["text_e2e"] = round(seconds, 3)

    def mark_sentence_end(self) -> None:
        self._sentence_ended = True

    def mark_tts_first_chunk(self, seconds: float) -> None:
        if seconds > 0:
            self._latency["tts_first_chunk"] = round(seconds, 3)

    def mark_audio_e2e(self, seconds: float) -> None:
        if seconds > 0:
            self._latency["audio_e2e"] = round(seconds, 3)

    def _ready(self) -> bool:
        if self.audio_output:
            return self._latency["audio_e2e"] is not None
        return self._sentence_ended and self._latency["text_e2e"] is not None

    def finalize(self, interrupted: bool = False) -> dict[str, Any] | None:
        if self._finalized or not self._turn_id:
            return None
        if not interrupted and not self._ready():
            return None
        self._finalized = True
        return {
            "turn_id": self._turn_id,
            "interrupted": interrupted,
            "latency_s": dict(self._latency),
        }
