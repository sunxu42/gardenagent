"""从 `.config.yaml` 加载服务端运行时配置（不读取密钥）。"""

from __future__ import annotations

import os

import yaml
from pydantic import BaseModel, Field

from src.config_paths import CONFIG_FILE


class TTSConfig(BaseModel):
    tts_provider_name: str = "HuoshanTTS"

    huoshan_tts_appid: str = ""
    huoshan_tts_access_token: str = ""
    huoshan_tts_resource_id: str = "volc.service_type.10029"
    huoshan_tts_ws_url: str = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"

    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    aliyun_appkey: str = ""
    aliyun_token: str = ""
    aliyun_host: str = "nls-gateway-cn-shanghai.aliyuncs.com"

    def get(self, key: str, default: str = "") -> str:
        return getattr(self, key, default)


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    bits_per_sample: int = 16

    asr_provider_name: str = "DoubaoStreamingASR"

    doubao_streaming_asr_appid: str = ""
    doubao_streaming_asr_access_token: str = ""
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    aliyun_appkey: str = ""
    aliyun_token: str = ""
    aliyun_host: str = "nls-gateway-cn-shanghai.aliyuncs.com"
    aliyun_max_sentence_silence: int = 8000

    def get(self, key: str, default: str = "") -> str:
        aliases = {
            "doubao_DOUBAO_STREAMING_ASR_APPID": "doubao_streaming_asr_appid",
            "doubao_DOUBAO_STREAMING_ASR_ACCESS_TOKEN": "doubao_streaming_asr_access_token",
            "aliyun_ACCESS_KEY_ID": "aliyun_access_key_id",
            "aliyun_ACCESS_KEY_SECRET": "aliyun_access_key_secret",
            "aliyun_APPKEY": "aliyun_appkey",
            "aliyun_TOKEN": "aliyun_token",
            "aliyun_HOST": "aliyun_host",
            "aliyun_MAX_SENTENCE_SILENCE": "aliyun_max_sentence_silence",
        }
        name = aliases.get(key, key)
        if hasattr(self, name):
            return getattr(self, name)
        if hasattr(self, key):
            return getattr(self, key)
        return default


class UnifiedConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8005
    input_modality: list[str] = Field(default_factory=lambda: ["text"])
    output_modality: list[str] = Field(default_factory=lambda: ["text"])
    handler_type: str = "default"
    agent_type: str = "yard_manager"

    audio_config: AudioConfig = Field(default_factory=AudioConfig)
    tts_config: TTSConfig = Field(default_factory=TTSConfig)


def _read_yaml(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def load_settings() -> UnifiedConfig:
    """仅读取 `.config.yaml`，不加载 `.env`。"""
    if not os.path.isfile(CONFIG_FILE):
        return UnifiedConfig()
    try:
        raw = _read_yaml(CONFIG_FILE)
    except (OSError, yaml.YAMLError):
        return UnifiedConfig()
    if not raw:
        return UnifiedConfig()
    try:
        return UnifiedConfig(**raw)
    except Exception:
        return UnifiedConfig()
