"""Affect / VAD wire payloads for WebSocket clients."""

from __future__ import annotations

import time
from typing import Any


def build_affect_appraised_payload(turn: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any] | None:
    user_affect = metrics.get("user_affect_vad") or metrics.get("utterance_vad")
    rel = metrics.get("relationship")
    policy = metrics.get("response_policy")
    target = metrics.get("agent_vad_target")
    if not isinstance(user_affect, dict) or not isinstance(rel, dict):
        return None
    return {
        "type": "affect_turn_appraised",
        "schema_version": metrics.get("schema_version", 2),
        "turn_id": turn.get("turn_id", ""),
        "user_text": turn.get("text", ""),
        "timestamp": int(time.time() * 1000),
        "user_affect_vad": user_affect,
        "user_weight": metrics.get("user_weight"),
        "relationship": rel,
        "interpersonal_cue": metrics.get("interpersonal_cue", ""),
        "response_policy": policy if isinstance(policy, dict) else {},
        "agent_vad_target": target if isinstance(target, dict) else None,
        "actuation_weight": metrics.get("actuation_weight") or metrics.get("weight"),
        "synthesis_rule": metrics.get("synthesis_rule"),
        "strategy_tags": metrics.get("strategy_tags"),
    }


def build_affect_settled_payload(turn_id: str, metrics: dict[str, Any]) -> dict[str, Any] | None:
    after = metrics.get("agent_vad_after")
    if not isinstance(after, dict):
        return None
    return {
        "type": "affect_turn_settled",
        "schema_version": metrics.get("schema_version", 2),
        "turn_id": turn_id,
        "timestamp": int(time.time() * 1000),
        "agent_vad_after": after,
        "agent_emotion": metrics.get("agent_emotion", "neutral"),
        "emotion_scale": metrics.get("emotion_scale", 4),
    }


def build_vad_turn_evaluated_v1(turn: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any] | None:
    utterance = metrics.get("utterance_vad")
    after = metrics.get("agent_vad_after")
    if not isinstance(utterance, dict) or not isinstance(after, dict):
        return None
    return {
        "type": "vad_turn_evaluated",
        "turn_id": turn.get("turn_id", ""),
        "user_text": turn.get("text", ""),
        "utterance_vad": utterance,
        "agent_vad_after": after,
        "timestamp": int(time.time() * 1000),
    }
