from typing import Any, Dict

from server.multimodal.common.importlib_registry import load_class


class TTSFactory:
    
    provider_to_class = {
        "HuoshanTTS": "server.multimodal.tts.backends.huoshan_double_streaming_tts.HuoshanTTS",
        "AliyunTTS": "server.multimodal.tts.backends.aliyun_streaming_tts.AliyunStreamingTTS",
        "DashscopeTTS": "server.multimodal.tts.backends.dashscope_streaming_tts.DashscopeStreamingTTS",
    }

    @classmethod
    def create(cls, provider_name: str, config: Dict[str, Any]) -> Any:

        class_type = cls.provider_to_class.get(provider_name)
        if not class_type:
            raise ValueError(f"Unsupported TTS provider: {provider_name}")
   
        tts_class = load_class(class_type)
        return tts_class(config)
