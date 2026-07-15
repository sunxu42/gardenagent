"""Agent kernel configuration loaded from `.config.yaml` (no secrets)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from agent.memory.core.triggers import (
    DEFAULT_KEYWORDS_EN,
    DEFAULT_KEYWORDS_ZH,
    DEFAULT_NEGATIVE_PATTERNS,
)
from shared.config.loader import read_config_yaml, reject_forbidden_yaml_keys
from shared.config.paths import (
    DEFAULT_EMOTION_STATE_PATH,
    DEFAULT_MCP_SERVERS_YAML,
    DEFAULT_PROMPTS_DIR,
    DEFAULT_SUBAGENTS_YAML,
    DEFAULT_WORKSPACE_DIR,
)

_DEFAULT_LLM_MODEL = "glm-4-flash"


class AgentConfig(BaseModel):
    """智能体内核配置（YAML）；运行时密钥由 `resolve_agent_runtime` 注入。"""

    skills_dir: str = "skills"
    workspace_dir: str = DEFAULT_WORKSPACE_DIR
    prompts_dir: str = DEFAULT_PROMPTS_DIR

    subagents_yaml: str = DEFAULT_SUBAGENTS_YAML
    mcp_servers_yaml: str = DEFAULT_MCP_SERVERS_YAML

    llm_base_url: Optional[str] = Field(default=None)
    llm_model_name: Optional[str] = Field(default=_DEFAULT_LLM_MODEL)

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

    emotion_enabled: bool = True
    emotion_alpha: float = 0.3
    emotion_beta: float = 0.05
    emotion_tau_sec: float = 3600.0
    emotion_state_path: str = DEFAULT_EMOTION_STATE_PATH
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

    eval_llm_model: Optional[str] = Field(default=None)
    eval_llm_base_url: Optional[str] = None

    prompt_composer_enabled: bool = True
    prompt_budget_enabled: bool = False
    prompt_stable_max_chars: int = 3000
    prompt_volatile_max_chars: int = 1500

    llm_api_key: Optional[str] = Field(default=None, repr=False)
    emotion_appraisal_api_key: Optional[str] = Field(default=None, repr=False)
    mem0_llm_api_key: Optional[str] = Field(default=None, repr=False)
    eval_llm_api_key: Optional[str] = Field(default=None, repr=False)
    mem0_history_db_path: Optional[str] = Field(default=None, repr=False)


# Backward-compatible alias used across the codebase.
Config = AgentConfig


def load_agent_settings(runtime_overrides: Optional[dict[str, Any]] = None) -> AgentConfig:
    """Load agent kernel settings from `.config.yaml` (no `.env`)."""
    raw = read_config_yaml()
    if runtime_overrides:
        raw = {**raw, **runtime_overrides}
    reject_forbidden_yaml_keys(raw)
    return AgentConfig(**raw)
