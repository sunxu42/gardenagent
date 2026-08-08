"""将服务端 YAML 配置与 `.env` 媒体凭证组合。"""

from __future__ import annotations

from shared.config.secrets import Secrets, load_secrets
from shared.config.server import ServerConfig, load_server_settings as load_settings

UnifiedConfig = ServerConfig


def needs_media_secrets(settings: ServerConfig) -> bool:
    """输入或输出含 audio 时需要 ASR/TTS 凭证。"""
    modalities = set(settings.input_modality) | set(settings.output_modality)
    return "audio" in modalities


def apply_media_secrets(settings: ServerConfig, secrets: Secrets) -> ServerConfig:
    """把 ASR/TTS 凭证注入 settings 副本。"""
    config = settings.model_copy(deep=True)

    config.audio_config.doubao_streaming_asr_appid = secrets.doubao_asr_appid or ""
    config.audio_config.doubao_streaming_asr_access_token = secrets.doubao_asr_token or ""
    config.audio_config.dashscope_api_key = secrets.dashscope_api_key or ""
    config.audio_config.aliyun_access_key_id = secrets.aliyun_access_key_id or ""
    config.audio_config.aliyun_access_key_secret = secrets.aliyun_access_key_secret or ""
    config.audio_config.aliyun_appkey = secrets.aliyun_appkey or ""
    config.audio_config.aliyun_token = secrets.aliyun_token or ""

    config.tts_config.huoshan_tts_appid = secrets.huoshan_appid or ""
    config.tts_config.huoshan_tts_access_token = secrets.huoshan_token or ""
    config.tts_config.dashscope_api_key = secrets.dashscope_api_key or ""
    config.tts_config.aliyun_access_key_id = secrets.aliyun_access_key_id or ""
    config.tts_config.aliyun_access_key_secret = secrets.aliyun_access_key_secret or ""
    config.tts_config.aliyun_appkey = secrets.aliyun_appkey or ""
    config.tts_config.aliyun_token = secrets.aliyun_token or ""

    return config


def resolve_server_runtime(
    settings: ServerConfig,
    secrets: Secrets | None = None,
) -> ServerConfig:
    """按需注入媒体凭证；纯文本模式不读取 secrets。"""
    if not needs_media_secrets(settings):
        return settings
    resolved_secrets = secrets if secrets is not None else load_secrets()
    return apply_media_secrets(settings, resolved_secrets)
