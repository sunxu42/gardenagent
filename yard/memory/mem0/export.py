"""从 Mem0 导出只读 memory.yaml（供 prompt-editor API / 前端查看，不参与对话注入）。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

from yard.memory.mem0.service import Mem0Service, _memory_text

MEMORY_YAML_REL = "memory/memory.yaml"


def memories_to_yaml_document(memories: list[dict[str, Any]], *, user_id: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for item in memories:
        text = _memory_text(item)
        if not text:
            continue
        meta = item.get("metadata") or {}
        entry: dict[str, Any] = {
            "id": item.get("id"),
            "memory": text,
        }
        if meta.get("category"):
            entry["category"] = meta["category"]
        if meta.get("source"):
            entry["source"] = meta["source"]
        if meta.get("pinned") is not None:
            entry["pinned"] = meta["pinned"]
        if item.get("created_at"):
            entry["created_at"] = item["created_at"]
        items.append(entry)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "note": "只读导出；权威记忆库为 Mem0/FAISS，编辑此文件不会影响检索。",
        "memories": items,
    }


def format_memory_yaml(memories: list[dict[str, Any]], *, user_id: str) -> str:
    doc = memories_to_yaml_document(memories, user_id=user_id)
    return yaml.safe_dump(
        doc,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


async def export_memory_yaml(
    service: Mem0Service,
    prompts_dir: str | Path,
    *,
    user_id: str | None = None,
) -> Path:
    """写入 yard/prompts/memory/memory.yaml，返回绝对路径。"""
    uid = user_id or service.default_user_id
    memories = await service.aget_all(user_id=uid, limit=200)
    root = Path(prompts_dir)
    out_dir = root / "memory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "memory.yaml"
    text = format_memory_yaml(memories, user_id=uid)
    out_path.write_text(text, encoding="utf-8")
    _log.info(f"Exported {len(memories)} memories to {out_path}")
    return out_path.resolve()
