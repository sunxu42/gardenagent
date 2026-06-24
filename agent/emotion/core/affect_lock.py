"""会话级情感状态锁定（内存，不持久化锁标记）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.emotion.core.relationship import derive_stage
from agent.emotion.core.vad import VAD


@dataclass
class AgentVadLock:
    ref_id: str
    vad: VAD


@dataclass
class RelationshipLock:
    ref_id: str
    trust: float
    warmth: float


def build_lock_state_payload(
    *,
    agent_lock: AgentVadLock | None,
    rel_lock: RelationshipLock | None,
) -> dict[str, Any]:
    rel: dict[str, Any] = {"locked": rel_lock is not None}
    if rel_lock is not None:
        rel.update({
            "ref_id": rel_lock.ref_id,
            "trust": rel_lock.trust,
            "warmth": rel_lock.warmth,
            "stage": derive_stage(rel_lock.trust, rel_lock.warmth),
        })
    vad_slice: dict[str, Any] = {"locked": agent_lock is not None}
    if agent_lock is not None:
        vad_slice.update({
            "ref_id": agent_lock.ref_id,
            "vad": agent_lock.vad.as_dict(),
            "emotion": agent_lock.ref_id,
        })
    return {"relationship": rel, "agent_vad": vad_slice}
