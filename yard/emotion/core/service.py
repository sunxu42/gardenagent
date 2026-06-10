"""EmotionService：按 user/device key 维护 VAD 状态，懒时间衰减 + 惯性更新 + 投影。"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Callable

from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.EMOTION)

from yard.emotion.core.appraisal_utils import sanitize_relationship_deltas
from yard.emotion.core.policy import ResponsePolicy, TurnAppraisalV2
from yard.emotion.core.relationship import (
    RelationshipState,
    apply_relationship_delta,
    decay_relationship,
    derive_stage,
)
from yard.emotion.core.store import EmotionStore
from yard.emotion.core.update import apply_appraisal, decay_over_time
from yard.emotion.core.vad import VAD, project
from yard.emotion.synthesis.mood_synthesizer import SynthesisResult, synthesize_response


class EmotionService:
    def __init__(
        self,
        *,
        key: str,
        baseline: VAD,
        store: EmotionStore,
        allowed_emotions: "set[str] | frozenset[str]",
        alpha: float,
        beta: float,
        tau_sec: float,
        rel_alpha: float = 0.3,
        rel_tau_sec: float = 7200.0,
        relationship_baseline: RelationshipState | None = None,
        appraisal_snapshot_max: int = 64,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._key = key
        self._baseline = baseline.clamp()
        self._store = store
        self._allowed = set(allowed_emotions)
        self._alpha = alpha
        self._beta = beta
        self._tau = tau_sec
        self._rel_alpha = rel_alpha
        self._rel_tau = rel_tau_sec
        self._clock = clock
        self._max_snapshots = max(8, int(appraisal_snapshot_max))
        self.last_render: tuple[str, int] = ("neutral", 4)
        self.last_appraisal_target: VAD | None = None
        self.last_appraisal_weight: float | None = None
        self.last_response_policy: ResponsePolicy | None = None
        self.last_user_emotion_label: str | None = None
        self.last_interpersonal_cue: str | None = None
        self.last_user_v: float = 0.0
        self._last_synthesis: SynthesisResult | None = None
        self._last_user_affect_display: VAD | None = None
        self._appraisal_snapshots: OrderedDict[str, dict] = OrderedDict()
        self._appraisal_snapshot_listener: Callable[[str], None] | None = None
        self._turn_snapshot_cache: tuple[str, int] | None = None

        rel_base = (relationship_baseline or RelationshipState()).clamp()
        self._relationship_baseline = rel_base
        rec = store.get(key)
        if rec and isinstance(rec.get("vad"), dict):
            self._vad = VAD.from_dict(rec["vad"])
            self._updated_at = float(rec.get("updated_at") or self._clock())
        else:
            self._vad = self._baseline
            self._updated_at = self._clock()

        if rec and isinstance(rec.get("relationship"), dict):
            self._relationship = RelationshipState.from_dict(rec["relationship"])
        else:
            self._relationship = RelationshipState(
                trust=rel_base.baseline_trust,
                warmth=rel_base.baseline_warmth,
                baseline_trust=rel_base.baseline_trust,
                baseline_warmth=rel_base.baseline_warmth,
                updated_at=self._clock(),
            )

    def begin_turn(self) -> None:
        self._turn_snapshot_cache = None

    def end_turn(self) -> None:
        self._turn_snapshot_cache = None

    def _clear_turn_ephemeral(self) -> None:
        """清空本轮/跨轮内存缓存，不改动持久化 VAD。"""
        self.last_render = ("neutral", 4)
        self.last_appraisal_target = None
        self.last_appraisal_weight = None
        self.last_response_policy = None
        self.last_user_emotion_label = None
        self.last_interpersonal_cue = None
        self.last_user_v = 0.0
        self._last_synthesis = None
        self._last_user_affect_display = None
        self._appraisal_snapshots.clear()
        self._turn_snapshot_cache = None

    def reset_to_defaults(self) -> VAD:
        """将助手 VAD 与关系重置为人设 baseline，并写回 EmotionStore。"""
        now = self._clock()
        rel_base = self._relationship_baseline
        self._vad = self._baseline.clamp()
        self._updated_at = now
        self._relationship = RelationshipState(
            trust=rel_base.baseline_trust,
            warmth=rel_base.baseline_warmth,
            baseline_trust=rel_base.baseline_trust,
            baseline_warmth=rel_base.baseline_warmth,
            updated_at=now,
        )
        self._clear_turn_ephemeral()
        self._persist()
        _log.info(f"EmotionService 已重置为 baseline key={self._key}")
        return self._vad

    def _decay_to_now(self) -> None:
        now = self._clock()
        dt = now - self._updated_at
        if dt > 0:
            self._vad = decay_over_time(self._vad, self._baseline, dt_sec=dt, tau_sec=self._tau)
            self._updated_at = now

    def _decay_relationship_to_now(self) -> None:
        now = self._clock()
        dt = now - self._relationship.updated_at
        if dt > 0 and self._rel_tau > 0:
            self._relationship = decay_relationship(
                self._relationship, dt_sec=dt, tau_sec=self._rel_tau
            )
            self._relationship = RelationshipState(
                trust=self._relationship.trust,
                warmth=self._relationship.warmth,
                baseline_trust=self._relationship.baseline_trust,
                baseline_warmth=self._relationship.baseline_warmth,
                updated_at=now,
            )

    def _persist(self) -> None:
        try:
            self._store.set(
                self._key,
                self._vad,
                updated_at=self._updated_at,
                relationship=self._relationship,
            )
        except Exception as e:
            _log.warning(f"EmotionService 持久化失败: {e!r}")

    def _store_snapshot(self, key: str, snap: dict) -> None:
        self._appraisal_snapshots[key] = snap
        self._appraisal_snapshots.move_to_end(key)
        while len(self._appraisal_snapshots) > self._max_snapshots:
            self._appraisal_snapshots.popitem(last=False)

    def current(self) -> VAD:
        self._decay_to_now()
        return self._vad

    def baseline(self) -> VAD:
        return self._baseline

    def relationship(self) -> RelationshipState:
        self._decay_relationship_to_now()
        return self._relationship.clamp()

    def apply_relationship_delta(
        self,
        *,
        trust_delta: float,
        warmth_delta: float,
        weight: float,
    ) -> RelationshipState:
        self._decay_relationship_to_now()
        self._relationship = apply_relationship_delta(
            self._relationship,
            trust_delta=trust_delta,
            warmth_delta=warmth_delta,
            weight=weight,
            alpha=self._rel_alpha,
        )
        self._persist()
        return self._relationship

    def apply(self, target: VAD, *, weight: float = 1.0, source: str = "llm") -> VAD:
        self._decay_to_now()
        self._vad = apply_appraisal(
            self._vad, target.clamp(), self._baseline,
            alpha=self._alpha, beta=self._beta, weight=weight,
        )
        self._updated_at = self._clock()
        self._persist()
        _log.debug(f"emotion.apply source={source} -> {self._vad.as_dict()}")
        return self._vad

    def apply_v2_turn(self, appraisal: TurnAppraisalV2, synthesis: SynthesisResult) -> VAD:
        appraisal = sanitize_relationship_deltas(appraisal)
        self._last_user_affect_display = appraisal.user_vad().clamp()
        self.apply_relationship_delta(
            trust_delta=appraisal.trust_delta,
            warmth_delta=appraisal.warmth_delta,
            weight=appraisal.rel_weight,
        )
        target = synthesis.actuation.vad_target
        weight = synthesis.actuation.weight
        self.mark_last_appraisal(target, weight)
        self.last_response_policy = synthesis.policy
        self.last_user_emotion_label = synthesis.user_emotion_label
        self.last_interpersonal_cue = appraisal.interpersonal_cue
        self.last_user_v = float(appraisal.user_v)
        self._last_synthesis = synthesis
        return self.apply(target, weight=weight, source="appraisal_v2")

    def mark_last_appraisal(self, target: VAD, weight: float) -> None:
        self.last_appraisal_target = target.clamp()
        self.last_appraisal_weight = max(0.0, min(1.0, float(weight)))

    def set_appraisal_snapshot_listener(self, listener: Callable[[str], None] | None) -> None:
        """注册 digest 快照就绪回调（Handler 用于推送 vad_turn_evaluated）。"""
        self._appraisal_snapshot_listener = listener

    def _notify_appraisal_snapshot(self, digest: str) -> None:
        key = (digest or "").strip()
        if not key or self._appraisal_snapshot_listener is None:
            return
        try:
            self._appraisal_snapshot_listener(key)
        except Exception as e:
            _log.warning(f"EmotionService appraisal snapshot listener failed: {e!r}")

    def record_appraisal_snapshot(
        self,
        digest: str,
        appraisal: TurnAppraisalV2,
        synthesis: SynthesisResult,
    ) -> None:
        key = (digest or "").strip()
        if not key:
            return
        rel = self.relationship()
        stage = derive_stage(rel.trust, rel.warmth)
        user_affect = (
            self._last_user_affect_display.as_dict()
            if self._last_user_affect_display is not None
            else appraisal.user_vad().as_dict()
        )
        agent_target = synthesis.actuation.vad_target.as_dict()
        agent_after = self.current().as_dict()
        emotion_label, emotion_scale = self.snapshot_for_turn()
        snap = {
            "schema_version": 2,
            "user_affect_vad": user_affect,
            "user_weight": float(appraisal.user_weight),
            "relationship": {
                "trust": rel.trust,
                "warmth": rel.warmth,
                "stage": stage,
                "trust_delta": float(appraisal.trust_delta),
                "warmth_delta": float(appraisal.warmth_delta),
                "rel_weight": float(appraisal.rel_weight),
            },
            "interpersonal_cue": appraisal.interpersonal_cue or "",
            "response_policy": synthesis.policy.model_dump(),
            "agent_vad_target": agent_target,
            "agent_vad_after": agent_after,
            "actuation_weight": float(synthesis.actuation.weight),
            "agent_emotion": emotion_label,
            "emotion_scale": int(emotion_scale),
            "synthesis_rule": synthesis.rule_id,
            "strategy_tags": synthesis.tags.as_dict(),
            "speech_rate": int(synthesis.actuation.speech_rate),
            "pitch": int(synthesis.actuation.pitch),
            "loudness_rate": int(synthesis.actuation.loudness_rate),
            "tts_emotion": synthesis.actuation.tts_emotion,
            "tts_emotion_scale": int(synthesis.actuation.tts_emotion_scale),
            "weight": synthesis.actuation.weight,
            "utterance_vad": user_affect,
        }
        self._store_snapshot(key, snap)
        self._notify_appraisal_snapshot(key)

    def notify_appraisal_ready(self, digest: str) -> None:
        """Appraisal 因 digest 去重跳过时，仍用已有快照通知 UI 对齐 pending 轮次。"""
        self._notify_appraisal_snapshot(digest)

    def get_appraisal_snapshot(self, digest: str) -> dict | None:
        key = (digest or "").strip()
        if not key:
            return None
        snap = self._appraisal_snapshots.get(key)
        if snap is not None:
            self._appraisal_snapshots.move_to_end(key)
        return dict(snap) if isinstance(snap, dict) else None

    def snapshot_for_turn(self, *, force: bool = False) -> tuple[str, int]:
        """每轮生成前调用：投影当前状态并缓存，供本轮 TTS 读取。"""
        if not force and self._turn_snapshot_cache is not None:
            return self._turn_snapshot_cache
        vad = self.current()
        self.last_render = project(vad, self._allowed)
        self._turn_snapshot_cache = self.last_render
        return self.last_render

    def build_settled_metrics(self) -> dict:
        """回复结束后刷新助手 VAD / 情绪标签，供 affect_turn_settled 使用。"""
        emotion, scale = self.snapshot_for_turn(force=True)
        syn = self._last_synthesis
        current = self.current().as_dict()
        target = (
            self.last_appraisal_target.as_dict()
            if self.last_appraisal_target is not None
            else dict(current)
        )
        return {
            "schema_version": 2,
            "utterance_vad": target,
            "agent_vad_after": current,
            "agent_emotion": emotion,
            "emotion_scale": int(scale),
            "synthesis_rule": syn.rule_id if syn is not None else None,
        }

    def synthesize_and_apply_v2(self, appraisal: TurnAppraisalV2) -> VAD | None:
        rel = self.relationship()
        synthesis = synthesize_response(appraisal, rel, self._baseline)
        return self.apply_v2_turn(appraisal, synthesis)

    def last_synthesis(self) -> SynthesisResult | None:
        return self._last_synthesis
