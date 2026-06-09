"""按 user/device key 的 VAD 状态持久化（JSON 文件）。"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Optional

from loguru import logger

from yard.emotion.core.relationship import RelationshipState
from yard.emotion.core.vad import VAD


class EmotionStore:
    def __init__(self, path: str) -> None:
        self._path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def _load(self) -> dict[str, Any]:
        if not os.path.isfile(self._path):
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("EmotionStore 读取失败，忽略旧值: {!r}", e)
            return {}

    def _atomic_write(self, data: dict[str, Any]) -> None:
        d = os.path.dirname(os.path.abspath(self._path))
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self._path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def get(self, key: str) -> Optional[dict[str, Any]]:
        return self._load().get(key)

    def set(
        self,
        key: str,
        vad: VAD,
        *,
        updated_at: float,
        relationship: RelationshipState | None = None,
    ) -> None:
        data = self._load()
        entry: dict[str, Any] = {
            "vad": vad.clamp().as_dict(),
            "updated_at": float(updated_at),
        }
        if relationship is not None:
            entry["relationship"] = relationship.clamp().as_dict()
        elif isinstance((existing := data.get(key)), dict) and isinstance(existing.get("relationship"), dict):
            entry["relationship"] = existing["relationship"]
        data[key] = entry
        self._atomic_write(data)
