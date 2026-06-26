"""Unit tests for eval API response caching."""

from __future__ import annotations

import time
from pathlib import Path

from eval.api.response_cache import StampCache, directory_content_stamp


def test_directory_content_stamp_uses_latest_file_mtime(tmp_path: Path) -> None:
    older = tmp_path / "a.yaml"
    newer = tmp_path / "b.yaml"
    older.write_text("a: 1", encoding="utf-8")
    time.sleep(0.01)
    newer.write_text("b: 2", encoding="utf-8")

    stamp = directory_content_stamp(tmp_path, "**/*.yaml")

    assert stamp >= newer.stat().st_mtime


def test_stamp_cache_reuses_value_for_same_stamp() -> None:
    cache: StampCache[int] = StampCache(ttl_seconds=30.0)
    calls = 0

    def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert cache.get((1.0,), factory) == 1
    assert cache.get((1.0,), factory) == 1
    assert calls == 1


def test_stamp_cache_rebuilds_when_stamp_changes() -> None:
    cache: StampCache[int] = StampCache(ttl_seconds=30.0)
    calls = 0

    def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert cache.get((1.0,), factory) == 1
    assert cache.get((2.0,), factory) == 2
    assert calls == 2
