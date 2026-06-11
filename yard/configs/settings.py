"""从 `.config.yaml` 加载运行时配置（不读取密钥）。"""

from __future__ import annotations

import os
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

from yard.configs.paths import CONFIG_FILE
from yard.memory.core.triggers import (
    DEFAULT_KEYWORDS_EN,
    DEFAULT_KEYWORDS_ZH,
    DEFAULT_NEGATIVE_PATTERNS,
)

_DEFAULT_LLM_MODEL = "glm-4-flash"

_FORBIDDEN_YAML_KEYS = frozenset(
    {
        "llm_api_key",
        "emotion_appraisal_api_key",
        "mem0_llm_api_key",
        "eval_llm_api_key",
        "llm_tool_calling",
    }
)


class Config(BaseModel):
    """Yard 智能体内核配置（YAML）；运行时密钥由 `resolve` 注入。"""

    skills_dir: str = "skills"
    workspace_dir: str = "yard/workspace"
    prompts_dir: str = "yard/prompts"

    subagents_yaml: str = "yard/configs/subagents.yaml"
    mcp_servers_yaml: str = "yard/configs/mcp_servers.yaml"

    llm_base_url: Optional[str] = Field(default=None)
    llm_model_name: Optional[str] = Field(default=_DEFAULT_LLM_MODEL)

    # --- Mem0 OSS 长期记忆 ---
    memory_enabled: bool = False
    mem0_user_id: str = "default"
    mem0_faiss_path: Optional[str] = None
    mem0_collection_name: str = "garden_memories"
    mem0_top_k: int = 6
    mem0_inject_max_chars: int = 2000
    mem0_llm_model: Optional[str] = None
    mem0_embedding_model: Optional[str] = None
    mem0_embedding_dims: int = 1536
    mem0_llm_base_url: Optional[str] = None

    # --- memory debug logging ---
    memory_debug_log_enabled: bool = False
    memory_debug_log_max_chars: int = 500

    memory_explicit_keyword_enabled: bool = True
    memory_explicit_keywords_zh: list[str] = Field(
        default_factory=lambda: list(DEFAULT_KEYWORDS_ZH)
    )
    memory_explicit_keywords_en: list[str] = Field(
        default_factory=lambda: list(DEFAULT_KEYWORDS_EN)
    )
    memory_explicit_negative_patterns: list[str] = Field(
        default_factory=lambda: list(DEFAULT_NEGATIVE_PATTERNS)
    )
    memory_explicit_weak_zh_enabled: bool = False
    memory_explicit_weak_en_enabled: bool = False

    memory_session_flush_on_summarization: bool = True
    memory_session_flush_idle_sec: int = 300
    memory_session_flush_poll_sec: int = 30
    memory_session_flush_on_shutdown: bool = True
    memory_journal_on_heartbeat: bool = True

    # --- 情绪表达子系统 ---
    emotion_enabled: bool = True
    emotion_alpha: float = 0.3
    emotion_beta: float = 0.05
    emotion_tau_sec: float = 3600.0
    emotion_state_path: str = "yard/workspace/emotion/emotion_state.json"
    emotion_user_key: str = "default"
    emotion_allowed: list[str] = Field(
        default_factory=lambda: [
            "happy", "sad", "angry", "fear", "hate", "surprised", "neutral",
        ]
    )
    emotion_appraisal_enabled: bool = True
    emotion_appraisal_model: Optional[str] = Field(default=None)
    emotion_appraisal_temperature: float = 0.1
    emotion_appraisal_max_user_chars: int = 2000
    emotion_appraisal_base_url: Optional[str] = None

    # --- DeepEval 情绪支持评测 ---
    eval_llm_model: Optional[str] = Field(default=None)
    eval_llm_base_url: Optional[str] = None

    # --- Prompt Composer ---
    prompt_composer_enabled: bool = False
    prompt_budget_enabled: bool = False
    prompt_stable_max_chars: int = 3000
    prompt_volatile_max_chars: int = 1500

    # --- 运行时字段（由 resolve 填充，勿写入 YAML）---
    llm_api_key: Optional[str] = Field(default=None, repr=False)
    emotion_appraisal_api_key: Optional[str] = Field(default=None, repr=False)
    mem0_llm_api_key: Optional[str] = Field(default=None, repr=False)
    eval_llm_api_key: Optional[str] = Field(default=None, repr=False)
    mem0_history_db_path: Optional[str] = Field(default=None, repr=False)


def _read_yaml(file_path: str) -> dict[str, Any]:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _reject_forbidden_yaml_keys(raw: dict[str, Any]) -> None:
    found = _FORBIDDEN_YAML_KEYS.intersection(raw.keys())
    if not found:
        return
    names = ", ".join(sorted(found))
    raise ValueError(
        f".config.yaml 含不允许的密钥/废弃字段: {names}。"
        " API Key 请写入 .env；llm_tool_calling 已移除。"
    )


def load_settings(runtime_overrides: Optional[dict[str, Any]] = None) -> Config:
    """仅读取 `.config.yaml`，不加载 `.env`。"""
    raw = _read_yaml(CONFIG_FILE) if os.path.isfile(CONFIG_FILE) else {}
    if runtime_overrides:
        raw = {**raw, **runtime_overrides}
    _reject_forbidden_yaml_keys(raw)
    return Config(**raw)
