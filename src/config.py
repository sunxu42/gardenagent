
import os
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
import yaml

CWD = os.getcwd()
DEFAULT_CONFIG_FILE = os.path.join(CWD, ".config.yaml")
DEFAULT_ENV_FILE = os.path.join(CWD, ".env")

load_dotenv(DEFAULT_ENV_FILE)


class TTSConfig(BaseModel):
    
    tts_provider_name: str = "HuoshanTTS" # "HuoshanTTS" or "AliyunStreamingTTS"
    
    huoshan_tts_appid: str = os.getenv("HUOSHAN_APPID", "")
    huoshan_tts_access_token: str = os.getenv("HUOSHAN_ACCESS_TOKEN", "")
    huoshan_tts_resource_id: str = "volc.service_type.10029"
    huoshan_tts_ws_url: str = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"

    # 长期阿里云配置
    aliyun_access_key_id: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    aliyun_access_key_secret: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    # 短期阿里云配置
    aliyun_appkey: str = os.getenv("ALIYUN_APPKEY", "")
    aliyun_token: str = os.getenv("ALIYUN_TOKEN", "")
    aliyun_host: str = "nls-gateway-cn-shanghai.aliyuncs.com"

    def get(self, key: str, default: str = ""):
        return getattr(self, key, default)


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    bits_per_sample: int = 16

    asr_provider_name: str = "DoubaoStreamingASR" # "DoubaoStreamingASR" or "AliyunStreamingASR"

    doubao_streaming_asr_appid: str = os.getenv("DOUBAO_STREAMING_ASR_APPID", "")
    doubao_streaming_asr_access_token: str = os.getenv("DOUBAO_STREAMING_ASR_ACCESS_TOKEN", "")
    # 长期阿里云配置
    aliyun_access_key_id: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    aliyun_access_key_secret: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    # 短期阿里云配置
    aliyun_appkey: str = os.getenv("ALIYUN_APPKEY", "")
    aliyun_token: str = os.getenv("ALIYUN_TOKEN", "")
    aliyun_host: str = "nls-gateway-cn-shanghai.aliyuncs.com"
    aliyun_max_sentence_silence: int = 8000

    def get(self, key: str, default=""):
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


class LoggingConfig(BaseModel):
    log_level: str = "INFO"
    log_file: str = "logs/websocket_server.log"
    log_rotation: str = "1 day"
    log_retention: str = "7 days"
    disable_modules: list[str] = []

class UnifiedConfig(BaseModel):


    host: str = "0.0.0.0"
    port: int = 8005
    input_modality: list[str] = ["text"] # ["text", "audio"] 
    output_modality: list[str] = ["text"] #["text", "audio"] 
    handler_type: str = "default"
    agent_type: str = "yard_manager"

    audio_config: AudioConfig = Field(default_factory=AudioConfig)
    tts_config: TTSConfig = Field(default_factory=TTSConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _read_yaml(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def load_config() -> UnifiedConfig:
    if not os.path.isfile(DEFAULT_CONFIG_FILE):
        return UnifiedConfig()
    try:
        raw = _read_yaml(DEFAULT_CONFIG_FILE)
    except (OSError, yaml.YAMLError):
        return UnifiedConfig()
    if not raw:
        return UnifiedConfig()
    try:
        return UnifiedConfig(**raw)
    except Exception:
        return UnifiedConfig()