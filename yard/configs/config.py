import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import yaml

from yard.memory.core.triggers import (
    DEFAULT_KEYWORDS_EN,
    DEFAULT_KEYWORDS_ZH,
    DEFAULT_NEGATIVE_PATTERNS,
)
from yard.memory.mem0.config import resolve_faiss_path

CWD = os.getcwd()
DEFAULT_CONFIG_FILE = os.path.join(CWD, ".config.yaml")
DEFAULT_ENV_FILE = os.path.join(CWD, ".env")
PROVIDER_SETTINGS = {
    "glm": {
        "api_key_env": "GLM_OPENAI_API_KEY",
        "base_url_env": "GLM_OPENAI_BASE_URL",
        "default_api_key": None,
        "default_base_url": None,
    },
    "ollama": {
        "api_key_env": "OLLAMA_OPENAI_API_KEY",
        "base_url_env": "OLLAMA_OPENAI_BASE_URL",
        "default_api_key": None,
        "default_base_url": None,
    },
}

load_dotenv(DEFAULT_ENV_FILE)

_DEFAULT_LLM_MODEL = "glm-4-flash"


class Config(BaseModel):
    skills_dir: str = "skills"
    workspace_dir: str = "yard/workspace"
    prompts_dir: str = "yard/prompts"

    subagents_yaml: str = "yard/configs/subagents.yaml"
    mcp_servers_yaml: str = "yard/configs/mcp_servers.yaml"

    llm_provider: Optional[str] = Field(default="glm")
    llm_api_key: Optional[str] = Field(default=None)
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

    # --- session → Mem0 批量写入（与 30min heartbeat 解耦）---
    # LangGraph 对话摘要（上下文压缩）完成后 flush 当前 thread
    memory_session_flush_on_summarization: bool = True
    # 上一轮对话结束后空闲多久再 flush（秒）；0 表示关闭空闲 flush
    memory_session_flush_idle_sec: int = 300
    # 空闲检测轮询间隔（秒）
    memory_session_flush_poll_sec: int = 30
    # 进程退出前 flush 兜底
    memory_session_flush_on_shutdown: bool = True
    # 是否在 heartbeat 时同步 memory/YYYY-MM-DD.md 日记
    memory_journal_on_heartbeat: bool = True

    # --- 情绪表达子系统 ---
    emotion_enabled: bool = True
    emotion_alpha: float = 0.3          # 朝 appraisal 目标靠拢系数（惯性）
    emotion_beta: float = 0.05          # 会话内向基线回归系数
    emotion_tau_sec: float = 3600.0     # 跨会话时间衰减时间常数（秒）
    emotion_state_path: str = "yard/workspace/emotion/emotion_state.json"
    emotion_user_key: str = "default"   # user/device 持久化键（单用户兜底）
    emotion_allowed: list[str] = Field(
        default_factory=lambda: [
            "happy", "sad", "angry", "fear", "hate", "surprised", "neutral",
        ]
    )
    # 用户话 → VAD 前置判定（优先取 .config.yaml；为空时回退 llm_model_name）
    emotion_appraisal_enabled: bool = True
    emotion_appraisal_model: Optional[str] = Field(default=None)
    emotion_appraisal_temperature: float = 0.1
    emotion_appraisal_max_user_chars: int = 2000

    # --- 三路 API Key 路由（不填则 fallback 到主模型 key）---
    emotion_appraisal_api_key: Optional[str] = None
    emotion_appraisal_base_url: Optional[str] = None
    mem0_llm_api_key: Optional[str] = None
    mem0_llm_base_url: Optional[str] = None


def _read_yaml(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _apply_llm_provider(config: Config) -> None:
    provider = (config.llm_provider or "").lower()
    settings = PROVIDER_SETTINGS.get(provider)
    if settings is None:
        supported = ", ".join(sorted(PROVIDER_SETTINGS))
        raise ValueError(
            f"Unsupported LLM provider: {config.llm_provider!r}. "
            f"Supported providers: {supported}"
        )

    config.llm_api_key = _first_non_empty(
        config.llm_api_key,
        os.getenv(settings["api_key_env"]),
        settings["default_api_key"],
    )
    config.llm_base_url = _first_non_empty(
        config.llm_base_url,
        os.getenv(settings["base_url_env"]),
        settings["default_base_url"],
    )
    config.llm_model_name = _first_non_empty(config.llm_model_name) or _DEFAULT_LLM_MODEL

    if not config.llm_api_key or not config.llm_base_url:
        raise ValueError(
            f"LLM API key and base url are required for provider {provider!r} "
            f"and model {config.llm_model_name!r}"
        )


def _apply_memory_settings(config: Config) -> None:
    if not config.memory_enabled:
        return

    embed_model = config.mem0_embedding_model or os.getenv("MEM0_EMBEDDING_MODEL")
    if not embed_model:
        raise ValueError(
            "memory_enabled=true 需要配置 mem0_embedding_model（.config.yaml）"
            " 或环境变量 MEM0_EMBEDDING_MODEL"
        )
    config.mem0_embedding_model = embed_model

    dims_env = os.getenv("MEM0_EMBEDDING_DIMS")
    if dims_env:
        try:
            config.mem0_embedding_dims = int(dims_env)
        except ValueError:
            pass

    resolve_faiss_path(config).mkdir(parents=True, exist_ok=True)


def _apply_api_key_fallbacks(config: Config) -> None:
    """子系统专用 Key 未配置时回退到主模型凭证。"""
    if not config.emotion_appraisal_api_key:
        config.emotion_appraisal_api_key = config.llm_api_key
    if not config.emotion_appraisal_base_url:
        config.emotion_appraisal_base_url = config.llm_base_url
    if not config.mem0_llm_api_key:
        config.mem0_llm_api_key = config.llm_api_key
    if not config.mem0_llm_base_url:
        config.mem0_llm_base_url = config.llm_base_url

    config.emotion_appraisal_model = (
        _first_non_empty(config.emotion_appraisal_model) or config.llm_model_name
    )


def load_config(runtime_config: Optional[dict] = None) -> Config:
    raw = _read_yaml(DEFAULT_CONFIG_FILE) if os.path.isfile(DEFAULT_CONFIG_FILE) else {}
    if runtime_config:
        raw.update(runtime_config)

    config = Config(**raw)
    _apply_llm_provider(config)
    _apply_memory_settings(config)
    _apply_api_key_fallbacks(config)
    return config
