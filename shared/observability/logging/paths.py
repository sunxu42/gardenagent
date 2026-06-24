from __future__ import annotations

from datetime import date
from pathlib import Path

from shared.config.paths import REPO_ROOT, RUNTIME_DIR


def resolve_log_dir() -> Path:
    from shared.config.secrets import load_secrets

    override = (load_secrets().garden_log_dir or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (RUNTIME_DIR / "logs").resolve()


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
