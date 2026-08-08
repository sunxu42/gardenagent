"""Conversation turn orchestration — ASR final → affect events → settled."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from agent.emotion.llm.appraisal import user_text_digest
from server.protocol.affect import (
    build_affect_appraised_payload,
    build_affect_settled_payload,
    build_vad_turn_evaluated_v1,
)
from shared.observability.logging import set_turn_id
from shared.observability.logging.turn_log import log_emotion_settled
from shared.observability.logging.metrics import TurnMetricsAggregator


SendJsonFn = Callable[[dict[str, Any]], Awaitable[None]]
SessionAccessor = Callable[[], Any | None]


class TurnOrchestrator:
    """Deep module for per-turn state, timing, and affect wire events."""

    def __init__(
        self,
        *,
        session_id: str,
        client_id: str,
        send_json: SendJsonFn,
        session_accessor: SessionAccessor,
        metrics: TurnMetricsAggregator,
        session_context,
        log,
    ) -> None:
        self._session_id = session_id
        self._client_id = client_id
        self._send_json = send_json
        self._session_accessor = session_accessor
        self._metrics = metrics
        self._session_context = session_context
        self._log = log

        self.timing_stats: dict[str, float | None] = self._empty_timing_stats()
        self._last_asr_partial_time: float | None = None
        self._last_user_turn: dict[str, Any] | None = None
        self._emitted_appraised_turn_ids: set[str] = set()
        self._emitted_settled_turn_ids: set[str] = set()
        self._turn_seq = 0
        self._vad_pending_turns: list[dict[str, Any]] = []
        self._pending_settle: list[dict[str, Any]] = []

    @staticmethod
    def _empty_timing_stats() -> dict[str, float | None]:
        return {
            "user_voice_stop_time": None,
            "asr_stop_time": 0.0,
            "agent_first_token_time": 0.0,
            "tts_first_chunk_time": 0.0,
            "asr_recognition_latency": 0.0,
            "text_response_latency": 0.0,
            "audio_response_latency": 0.0,
        }

    def reset_session_state(self) -> None:
        self._emitted_appraised_turn_ids.clear()
        self._emitted_settled_turn_ids.clear()
        self._pending_settle.clear()
        self._vad_pending_turns.clear()

    def reset_timing_stats(self) -> None:
        self.timing_stats = self._empty_timing_stats()

    def update_session_id(self, session_id: str) -> None:
        self._session_id = session_id

    def record_user_voice_stop(self) -> None:
        self.timing_stats["user_voice_stop_time"] = time.time()

    def record_asr_partial(self) -> None:
        self._last_asr_partial_time = time.time()

    def begin_final_turn(self, text: str) -> str:
        """Register a final user turn; returns ``turn_id``."""
        captured_voice_stop = self.timing_stats["user_voice_stop_time"]
        captured_partial = self._last_asr_partial_time
        self._turn_seq += 1
        turn_id = f"{self._session_id or self._client_id}-turn-{self._turn_seq}"
        set_turn_id(turn_id)
        self._metrics.begin_turn(turn_id)
        self.reset_timing_stats()
        digest = user_text_digest(text)
        turn_record = {
            "turn_id": turn_id,
            "text": text,
            "digest": digest,
        }
        self._last_user_turn = turn_record
        self._vad_pending_turns.append(turn_record)
        asr_t = time.time()
        self.timing_stats["asr_stop_time"] = asr_t
        if captured_voice_stop is not None:
            self.timing_stats["asr_recognition_latency"] = asr_t - captured_voice_stop
            self.timing_stats["user_voice_stop_time"] = captured_voice_stop
        elif captured_partial is not None:
            self.timing_stats["asr_recognition_latency"] = asr_t - captured_partial
        self._last_asr_partial_time = None
        asr_sec = float(self.timing_stats["asr_recognition_latency"] or 0.0)
        if asr_sec > 0:
            self._metrics.mark_asr(asr_sec)
        return turn_id

    def current_turn_id(self) -> str:
        return f"{self._session_id or self._client_id}-turn-{self._turn_seq}"

    def asr_latency_sec(self) -> float:
        return float(self.timing_stats["asr_recognition_latency"] or 0.0)

    def on_appraisal_snapshot_ready(self, digest: str) -> None:
        import asyncio

        try:
            asyncio.get_running_loop().create_task(self.emit_vad_for_digest(digest))
        except RuntimeError:
            self._log.debug("VAD emit skipped: no running event loop")

    async def emit_vad_for_digest(self, digest: str) -> None:
        key = (digest or "").strip()
        if not key:
            return
        matching = [t for t in self._vad_pending_turns if t.get("digest") == key]
        if not matching:
            self._log.debug(f"VAD history skip: no pending turn for digest={key[:8]}")
            return
        session = self._session_accessor()
        metrics = session.vad_snapshot_for_digest(key) if session is not None else None
        if not isinstance(metrics, dict):
            self._log.debug("VAD history skip: vad snapshot unavailable")
            return

        is_v2 = metrics.get("schema_version") == 2 or isinstance(
            metrics.get("response_policy"), dict
        )

        for turn in matching:
            turn_id = str(turn.get("turn_id") or "").strip()
            if not turn_id:
                self._log.debug("VAD history skip: invalid turn_id")
                continue
            if is_v2:
                if turn_id not in self._emitted_appraised_turn_ids:
                    payload = build_affect_appraised_payload(turn, metrics)
                    if payload:
                        await self._send_json(payload)
                        self._emitted_appraised_turn_ids.add(turn_id)
                        self._log.debug(f"affect_turn_appraised emitted: turn_id={turn_id}")
                if turn_id not in self._emitted_settled_turn_ids and not any(
                    item.get("turn_id") == turn_id for item in self._pending_settle
                ):
                    self._pending_settle.append({"turn_id": turn_id, "turn": turn, "is_v2": True})
            elif turn_id not in self._emitted_settled_turn_ids and not any(
                item.get("turn_id") == turn_id for item in self._pending_settle
            ):
                self._pending_settle.append({"turn_id": turn_id, "turn": turn, "is_v2": False})

        self._vad_pending_turns = [t for t in self._vad_pending_turns if t.get("digest") != key]

    async def emit_settled_for_next_turn(self) -> None:
        if not self._pending_settle:
            return
        item = self._pending_settle.pop(0)
        turn_id = str(item.get("turn_id") or "").strip()
        if not turn_id or turn_id in self._emitted_settled_turn_ids:
            return
        session = self._session_accessor()
        metrics: dict[str, Any] | None = None
        if session is not None:
            session.end_emotion_turn()
            metrics = session.affect_settled_metrics()
        if not isinstance(metrics, dict):
            self._log.debug(f"settled skip: metrics unavailable turn_id={turn_id}")
            return

        if item.get("is_v2"):
            payload = build_affect_settled_payload(turn_id, metrics)
            if payload:
                await self._send_json(payload)
                self._emitted_settled_turn_ids.add(turn_id)
                with self._session_context():
                    set_turn_id(turn_id)
                    log_emotion_settled(metrics=metrics)
                after = metrics.get("agent_vad_after") or {}
                a_val = after.get("a") if isinstance(after, dict) else None
                self._log.debug(f"affect_turn_settled emitted: turn_id={turn_id}, a={a_val}")
        else:
            turn = item.get("turn") if isinstance(item.get("turn"), dict) else {"turn_id": turn_id}
            payload = build_vad_turn_evaluated_v1(turn, metrics)
            if payload:
                await self._send_json(payload)
                self._emitted_settled_turn_ids.add(turn_id)
                self._log.debug(f"vad_turn_evaluated emitted: turn_id={turn_id}")

    def mark_agent_first_token(self) -> float:
        first_t = time.time()
        self.timing_stats["agent_first_token_time"] = first_t
        voice_stop = self.timing_stats["user_voice_stop_time"]
        if voice_stop is not None:
            self.timing_stats["text_response_latency"] = first_t - voice_stop
        elif self.timing_stats["asr_stop_time"]:
            self.timing_stats["text_response_latency"] = (
                first_t - float(self.timing_stats["asr_stop_time"])
            )
        return float(self.timing_stats["text_response_latency"] or 0.0)

    def mark_tts_first_chunk(self) -> tuple[float, float]:
        now = time.time()
        self.timing_stats["tts_first_chunk_time"] = now
        voice_stop = self.timing_stats["user_voice_stop_time"]
        if voice_stop is not None:
            self.timing_stats["audio_response_latency"] = now - voice_stop
        elif self.timing_stats["agent_first_token_time"]:
            self.timing_stats["audio_response_latency"] = (
                now - float(self.timing_stats["agent_first_token_time"])
            )
        elif self.timing_stats["asr_stop_time"]:
            self.timing_stats["audio_response_latency"] = (
                now - float(self.timing_stats["asr_stop_time"])
            )
        tts_sec = 0.0
        if self.timing_stats["agent_first_token_time"]:
            tts_sec = now - float(self.timing_stats["agent_first_token_time"])
        return tts_sec, float(self.timing_stats["audio_response_latency"] or 0.0)
