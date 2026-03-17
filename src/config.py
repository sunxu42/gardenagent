
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# 加载环境变量（从项目根目录的 .env 文件）
load_dotenv()


def _get_env(key: str, default: str = '') -> str:
    """获取环境变量"""
    return os.getenv(key, default)


def _get_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    return int(os.getenv(key, str(default)))


class Config:
    
    # ==================== 通用配置 ====================
    # 音频通用配置（用于WebSocket）
    AUDIO_SAMPLE_RATE = _get_int('AUDIO_SAMPLE_RATE', 16000)
    AUDIO_CHANNELS = _get_int('AUDIO_CHANNELS', 1)
    AUDIO_BITS_PER_SAMPLE = _get_int('AUDIO_BITS_PER_SAMPLE', 16)
    
    # 日志通用配置
    LOG_LEVEL = _get_env('LOG_LEVEL', 'INFO')
    
    # ==================== WebSocket 配置 ====================
    WEBSOCKET_HOST = _get_env('WEBSOCKET_HOST', '0.0.0.0')
    WEBSOCKET_PORT = _get_int('WEBSOCKET_PORT', 8005)
    WEBSOCKET_LOG_FILE = _get_env('LOG_FILE', 'logs/websocket_server.log')
    HANDLER_TYPE = _get_env('HANDLER_TYPE', 'default')
    
    # ==================== ZeroMQ 配置 ====================
    ASR_LISTEN_ADDRESS = _get_env('ASR_LISTEN_ADDRESS', 'ipc:///tmp/asr_listen')
    ASR_PUBLISH_ADDRESS = _get_env('ASR_PUBLISH_ADDRESS', 'ipc:///tmp/asr_publish')
    TTS_LISTEN_ADDRESS = _get_env('TTS_LISTEN_ADDRESS', 'ipc:///tmp/tts_listen')
    TTS_PUBLISH_ADDRESS = _get_env('TTS_PUBLISH_ADDRESS', 'ipc:///tmp/tts_publish')
    CONTROL_BUS_ADDRESS = _get_env('CONTROL_BUS_ADDRESS', 'ipc:///tmp/control_bus')
    
    # ==================== ASR 配置 ====================
    ASR_PROVIDER = _get_env('ASR_PROVIDER', '')
    
    # 流式ASR配置（仅保留必需参数）
    DOUBAO_STREAMING_ASR_APPID = _get_env('DOUBAO_STREAMING_ASR_APPID', '')
    DOUBAO_STREAMING_ASR_ACCESS_TOKEN = _get_env('DOUBAO_STREAMING_ASR_ACCESS_TOKEN', '')
    
    # 阿里云ASR配置
    ALIYUN_ACCESS_KEY_ID = _get_env('ALIYUN_ACCESS_KEY_ID', '')
    ALIYUN_ACCESS_KEY_SECRET = _get_env('ALIYUN_ACCESS_KEY_SECRET', '')
    ALIYUN_APPKEY = _get_env('ALIYUN_APPKEY', '')
    ALIYUN_TOKEN = _get_env('ALIYUN_TOKEN', '')  # 可选，如果不提供则使用 access_key_id + access_key_secret 自动获取
    ALIYUN_HOST = _get_env('ALIYUN_HOST', 'nls-gateway-cn-shanghai.aliyuncs.com')
    ALIYUN_MAX_SENTENCE_SILENCE = _get_int('ALIYUN_MAX_SENTENCE_SILENCE', 8000)
    
    # ==================== TTS 配置 ====================
    TTS_PROVIDER = _get_env('TTS_PROVIDER', 'huoshan')
    TTS_LOG_FILE = _get_env('TTS_SERVICE_LOG', 'logs/tts_service.log')
    
    # 火山引擎TTS配置（仅保留必需参数）
    HUOSHAN_APPID = _get_env('HUOSHAN_APPID', '')
    HUOSHAN_ACCESS_TOKEN = _get_env('HUOSHAN_ACCESS_TOKEN', '')
    HUOSHAN_RESOURCE_ID = _get_env('HUOSHAN_RESOURCE_ID', '')
    HUOSHAN_WS_URL = _get_env('HUOSHAN_WS_URL', '')
    
    # 阿里云TTS配置
    ALIYUN_TTS_ACCESS_KEY_ID = _get_env('ALIYUN_TTS_ACCESS_KEY_ID', '')
    ALIYUN_TTS_ACCESS_KEY_SECRET = _get_env('ALIYUN_TTS_ACCESS_KEY_SECRET', '')
    ALIYUN_TTS_APPKEY = _get_env('ALIYUN_TTS_APPKEY', '')
    ALIYUN_TTS_TOKEN = _get_env('ALIYUN_TTS_TOKEN', '')  # 可选，如果不提供则使用 access_key_id + access_key_secret 自动获取
    ALIYUN_TTS_HOST = _get_env('ALIYUN_TTS_HOST', 'nls-gateway-cn-beijing.aliyuncs.com')


# ==================== 向后兼容的别名 ====================
# 为了保持现有代码的兼容性，提供别名类
class WebSocketConfig:
    """WebSocket配置（向后兼容）"""
    host = Config.WEBSOCKET_HOST
    port = Config.WEBSOCKET_PORT
    audio_sample_rate = Config.AUDIO_SAMPLE_RATE
    audio_channels = Config.AUDIO_CHANNELS
    audio_bits_per_sample = Config.AUDIO_BITS_PER_SAMPLE
    log_level = Config.LOG_LEVEL
    log_file = Config.WEBSOCKET_LOG_FILE
    handler_type = Config.HANDLER_TYPE


class TTSConfig:
    
    tts_provider_name = Config.TTS_PROVIDER
    
    huoshan_tts_appid = Config.HUOSHAN_APPID
    huoshan_tts_access_token = Config.HUOSHAN_ACCESS_TOKEN
    huoshan_tts_resource_id = Config.HUOSHAN_RESOURCE_ID
    huoshan_tts_ws_url = Config.HUOSHAN_WS_URL
    
    # 阿里云TTS配置
    aliyun_access_key_id = Config.ALIYUN_TTS_ACCESS_KEY_ID
    aliyun_access_key_secret = Config.ALIYUN_TTS_ACCESS_KEY_SECRET
    aliyun_appkey = Config.ALIYUN_TTS_APPKEY
    aliyun_token = Config.ALIYUN_TTS_TOKEN
    aliyun_host = Config.ALIYUN_TTS_HOST
    
    # ZeroMQ地址配置
    tts_listen_address = Config.TTS_LISTEN_ADDRESS
    tts_publish_address = Config.TTS_PUBLISH_ADDRESS
    
    
    def get(self, key: str, default: str = ''):
        return getattr(self, key, default)


class AudioConfig:
    asr_listen_address = Config.ASR_LISTEN_ADDRESS
    asr_publish_address = Config.ASR_PUBLISH_ADDRESS
    asr_provider_name = Config.ASR_PROVIDER
    doubao_DOUBAO_STREAMING_ASR_APPID = Config.DOUBAO_STREAMING_ASR_APPID
    doubao_DOUBAO_STREAMING_ASR_ACCESS_TOKEN = Config.DOUBAO_STREAMING_ASR_ACCESS_TOKEN
    aliyun_ACCESS_KEY_ID = Config.ALIYUN_ACCESS_KEY_ID
    aliyun_ACCESS_KEY_SECRET = Config.ALIYUN_ACCESS_KEY_SECRET
    aliyun_APPKEY = Config.ALIYUN_APPKEY
    aliyun_TOKEN = Config.ALIYUN_TOKEN
    aliyun_HOST = Config.ALIYUN_HOST
    aliyun_MAX_SENTENCE_SILENCE = Config.ALIYUN_MAX_SENTENCE_SILENCE

    def get(self, key: str, default: str = ''):
        return getattr(self, key, default)


# 逐步将配置迁移到UnifiedConfig中, 统一并简化配置管理,
class UnifiedConfig(BaseModel):
    input_modality: list[str] = ["text", "audio"] # 至少["text"]
    output_modality: list[str] = ["text", "audio"] # 至少["text"]


def load_config():
    # 从环境变量中加载配置并融合
    config = UnifiedConfig()
    if os.getenv('INPUT_MODALITY'):
        config.input_modality = os.getenv('INPUT_MODALITY').split(',')
    if os.getenv('OUTPUT_MODALITY'):
        config.output_modality = os.getenv('OUTPUT_MODALITY').split(',')
    return config