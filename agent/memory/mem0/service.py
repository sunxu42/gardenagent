"""Mem0 OSS 封装：add / search / get_all / update / delete。"""

from __future__ import annotations

import asyncio
from typing import Any

from agent.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

from agent.memory.mem0.config import build_mem0_config_dict

try:
    from mem0 import Memory
except ImportError:  # pragma: no cover
    Memory = None  # type: ignore[assignment,misc]


def _normalize_search_results(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        results = raw.get("results")
        if isinstance(results, list):
            return results
        return []
    if isinstance(raw, list):
        return raw
    return []


def _memory_text(item: dict[str, Any]) -> str:
    return str(item.get("memory") or item.get("content") or item.get("data") or "").strip()


class Mem0Service:
    def __init__(self, memory: Any, *, default_user_id: str = "default") -> None:
        self._memory = memory
        self.default_user_id = default_user_id

    @classmethod
    def create(cls, config: Any) -> Mem0Service:
        if Memory is None:
            raise ImportError("mem0ai 未安装，请执行: pip install mem0ai faiss-cpu")
        if not config.memory_enabled:
            raise ValueError("memory_enabled is false")
        config_dict = build_mem0_config_dict(config)
        _log.info(
            f"Initializing Mem0 OSS (FAISS path={config_dict['vector_store']['config']['path']})",
        )
        memory = Memory.from_config(config_dict)
        user_id = config.mem0_user_id or "default"
        return cls(memory, default_user_id=user_id)

    def add(
        self,
        messages: list[dict[str, str]] | str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> Any:
        uid = self._resolve_uid(user_id)
        return self._memory.add(
            messages,
            user_id=uid,
            metadata=metadata or {},
            infer=infer,
        )

    def search(
        self,
        query: str,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        uid = self._resolve_uid(user_id)
        k = limit or 100
        # mem0 不同版本参数名不一致（有的用 top_k，有的用 limit/user_id）。
        # 这里做一次兼容兜底，避免因参数名差异导致整轮报错。
        try:
            raw = self._memory.search(query, filters={"user_id": uid}, top_k=k)
        except TypeError:
            try:
                raw = self._memory.search(query, user_id=uid, limit=k)
            except TypeError:
                raw = self._memory.search(query, filters={"user_id": uid}, limit=k)
        return _normalize_search_results(raw)

    def get_all(self, *, user_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        uid = self._resolve_uid(user_id)
        try:
            raw = self._memory.get_all(filters={"user_id": uid}, top_k=limit)
        except TypeError:
            try:
                raw = self._memory.get_all(filters={"user_id": uid}, limit=limit)
            except TypeError:
                raw = self._memory.get_all(user_id=uid, limit=limit)
        if isinstance(raw, dict):
            results = raw.get("results")
            if isinstance(results, list):
                return results
        if isinstance(raw, list):
            return raw
        return []

    def update(self, memory_id: str, data: str) -> Any:
        return self._memory.update(memory_id, data=data)

    def delete(self, memory_id: str) -> Any:
        return self._memory.delete(memory_id)

    def delete_all_for_user(self, user_id: str | None = None) -> None:
        uid = self._resolve_uid(user_id)
        if hasattr(self._memory, "delete_all"):
            self._memory.delete_all(user_id=uid)
            return
        for item in self.get_all(user_id=uid, limit=10_000):
            memory_id = item.get("id")
            if memory_id:
                self.delete(str(memory_id))

    async def aadd(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.add, *args, **kwargs)

    async def asearch(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self.search, *args, **kwargs)

    async def aget_all(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self.get_all, *args, **kwargs)

    def _resolve_uid(self, user_id: str | None) -> str:
        uid = user_id if isinstance(user_id, str) else None
        if uid is not None:
            uid = uid.strip()
        default_uid = self.default_user_id if isinstance(self.default_user_id, str) else None
        if default_uid is not None:
            default_uid = default_uid.strip()
        return uid or default_uid or "default"

    @staticmethod
    def format_bullets(memories: list[dict[str, Any]], *, max_chars: int = 2000) -> str:
        lines: list[str] = []
        total = 0
        for item in memories:
            text = _memory_text(item)
            if not text:
                continue
            line = f"- {text}"
            if total + len(line) + 1 > max_chars:
                break
            lines.append(line)
            total += len(line) + 1
        return "\n".join(lines)
