"""In-process response caches for eval HTTP handlers."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


def directory_content_stamp(directory: Path, pattern: str) -> float:
    """Return the latest mtime among files matched under a directory."""

    if not directory.exists():
        return 0.0

    latest = directory.stat().st_mtime
    for path in directory.glob(pattern):
        if path.is_file():
            latest = max(latest, path.stat().st_mtime)
    return latest


@dataclass
class _StampCacheEntry(Generic[T]):
    value: T
    stamps: tuple[float, ...]
    cached_at: float


class StampCache(Generic[T]):
    """Cache values while source directory stamps and TTL remain valid."""

    def __init__(self, ttl_seconds: float = 30.0) -> None:
        self._ttl_seconds = ttl_seconds
        self._entry: _StampCacheEntry[T] | None = None

    def get(self, stamps: tuple[float, ...], factory: Callable[[], T]) -> T:
        """Return a cached value or rebuild it with ``factory``."""

        now = time.monotonic()
        entry = self._entry
        if entry is not None:
            if entry.stamps == stamps and (now - entry.cached_at) < self._ttl_seconds:
                return entry.value

        value = factory()
        self._entry = _StampCacheEntry(value=value, stamps=stamps, cached_at=now)
        return value

    def clear(self) -> None:
        """Drop the cached entry."""

        self._entry = None
