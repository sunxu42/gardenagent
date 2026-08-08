"""Combine agent YAML settings with `.env` secrets."""

from __future__ import annotations

from typing import Optional

from shared.config.agent import AgentConfig
from shared.config.secrets import Secrets


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


_DEFAULT_LLM_MODEL = "glm-4-flash"


def _resolve_platform_api_key(secrets: Secrets) -> str:
    key = secrets.dashscope_api_key
    if not key:
        raise ValueError("请在 .env 中配置 DASHSCOPE_API_KEY（阿里百炼 API Key）")
    return key


def resolve_agent_runtime(settings: AgentConfig, secrets: Secrets) -> AgentConfig:
    """Inject secrets into a copy of agent settings and validate prerequisites."""
    config = settings.model_copy(deep=True)
    platform_api_key = _resolve_platform_api_key(secrets)
    config.llm_api_key = platform_api_key
    config.llm_base_url = _first_non_empty(config.llm_base_url)
    config.llm_model_name = _first_non_empty(config.llm_model_name) or _DEFAULT_LLM_MODEL

    if not config.llm_base_url:
        raise ValueError("llm_base_url 必须在 .config.yaml 中配置")

    config.emotion_appraisal_api_key = platform_api_key
    config.emotion_appraisal_base_url = _first_non_empty(
        config.emotion_appraisal_base_url,
        config.llm_base_url,
    )
    config.mem0_llm_api_key = platform_api_key
    config.mem0_llm_base_url = _first_non_empty(
        config.mem0_llm_base_url,
        config.llm_base_url,
    )
    config.emotion_appraisal_model = (
        _first_non_empty(config.emotion_appraisal_model) or config.llm_model_name
    )
    config.eval_llm_api_key = platform_api_key
    config.eval_llm_base_url = _first_non_empty(
        config.eval_llm_base_url,
        config.llm_base_url,
    )
    config.eval_llm_model = (
        _first_non_empty(config.eval_llm_model) or config.llm_model_name
    )
    config.mem0_history_db_path = secrets.mem0_history_db_path

    return config


def resolve_yard_runtime(settings: AgentConfig, secrets: Secrets) -> AgentConfig:
    """Deprecated alias for :func:`resolve_agent_runtime`."""
    return resolve_agent_runtime(settings, secrets)
