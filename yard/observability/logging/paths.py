from __future__ import annotations

import os
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_log_dir() -> Path:
    override = os.getenv("GARDEN_LOG_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (REPO_ROOT / "logs").resolve()


def resolve_log_file(cfg_dir: str, cfg_file: str) -> Path:
    base = Path(cfg_dir)
    if not base.is_absolute():
        base = REPO_ROOT / base
    return (base / cfg_file).resolve()


def dated_filename(base: Path, day: date | None = None) -> Path:
    d = day or date.today()
    stem = base.stem
    suffix = base.suffix or ".jsonl"
    return base.parent / f"{stem}-{d.isoformat()}{suffix}"
