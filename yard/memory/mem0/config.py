"""从 GardenAI Config 构建 Mem0 OSS `Memory.from_config` 字典。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

COMPANION_EXTRACTION_HINT = (
    "Extract only durable facts about the user: preferences, food tastes, hobbies, "
    "relationships and names, recent life events. "
    "Do not extract: model instructions, API keys, one-off greetings, or meta chat."
)


def resolve_faiss_path(config: Any) -> Path:
    if config.mem0_faiss_path:
        return Path(config.mem0_faiss_path).expanduser().resolve()
    return Path(config.workspace_dir).resolve() / "memory" / "faiss"


def build_mem0_config_dict(config: Any) -> dict[str, Any]:
    """构建 Mem0 OSS 配置；调用方需保证 embedding 与 API 凭证已配置。"""
    faiss_path = resolve_faiss_path(config)
    faiss_path.mkdir(parents=True, exist_ok=True)

    llm_model = config.mem0_llm_model or config.llm_model_name
    embed_model = config.mem0_embedding_model
    if not embed_model:
        raise ValueError("mem0_embedding_model is required when memory is enabled")

    api_key = config.mem0_llm_api_key
    base_url = config.mem0_llm_base_url

    mem0_config: dict[str, Any] = {
        "version": "v1.1",
        "custom_instructions": COMPANION_EXTRACTION_HINT,
        "llm": {
            "provider": "openai",
            "config": {
                "model": llm_model,
                "api_key": api_key,
                "openai_base_url": base_url,
                "temperature": 0.1,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": embed_model,
                "api_key": api_key,
                "openai_base_url": base_url,
                "embedding_dims": config.mem0_embedding_dims,
            },
        },
        "vector_store": {
            "provider": "faiss",
            "config": {
                "collection_name": config.mem0_collection_name,
                "path": str(faiss_path),
                "distance_strategy": "cosine",
                "normalize_L2": True,
                # 必须与 embedder 实际向量维度一致（Mem0 FAISS 默认 1536，否则会 AssertionError）
                "embedding_model_dims": config.mem0_embedding_dims,
            },
        },
    }

    history_path = os.getenv("MEM0_HISTORY_DB_PATH")
    if history_path:
        mem0_config["history_db_path"] = history_path

    return mem0_config
