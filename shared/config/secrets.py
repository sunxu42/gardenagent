"""从 `.env` 加载密钥与运行时环境变量（与 YAML 配置分离）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

from shared.config.paths import ENV_FILE


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    return v


def _env(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    text = _strip_quotes(raw)
    return text if text else None


@dataclass(frozen=True)
class Secrets:
    """`.env` 中的凭证与少量运行时覆盖项。"""

    glm_api_key: str | None = None
    emotion_appraisal_api_key: str | None = None
    mem0_llm_api_key: str | None = None
    eval_llm_api_key: str | None = None

    doubao_asr_appid: str | None = None
    doubao_asr_token: str | None = None
    huoshan_appid: str | None = None
    huoshan_token: str | None = None
    aliyun_appkey: str | None = None
    aliyun_token: str | None = None
    aliyun_access_key_id: str | None = None
    aliyun_access_key_secret: str | None = None

    mem0_history_db_path: str | None = None
    garden_log_dir: str | None = None
    shared_state_backend: str | None = None


@lru_cache(maxsize=1)
def load_secrets() -> Secrets:
    """读取 `.env` 并解析为 `Secrets`（幂等，结果缓存）。"""
    load_dotenv(ENV_FILE)
    return Secrets(
        glm_api_key=_env("GLM_OPENAI_API_KEY"),
        emotion_appraisal_api_key=_env("EMOTION_APPRAISAL_API_KEY"),
        mem0_llm_api_key=_env("MEM0_LLM_API_KEY"),
        eval_llm_api_key=_env("EVAL_LLM_API_KEY"),
        doubao_asr_appid=_env("DOUBAO_STREAMING_ASR_APPID"),
        doubao_asr_token=_env("DOUBAO_STREAMING_ASR_ACCESS_TOKEN"),
        huoshan_appid=_env("HUOSHAN_APPID"),
        huoshan_token=_env("HUOSHAN_ACCESS_TOKEN"),
        aliyun_appkey=_env("ALIYUN_APPKEY"),
        aliyun_token=_env("ALIYUN_TOKEN"),
        aliyun_access_key_id=_env("ALIYUN_ACCESS_KEY_ID"),
        aliyun_access_key_secret=_env("ALIYUN_ACCESS_KEY_SECRET"),
        mem0_history_db_path=_env("MEM0_HISTORY_DB_PATH"),
        garden_log_dir=_env("GARDEN_LOG_DIR"),
        shared_state_backend=_env("SHARED_STATE_BACKEND"),
    )
