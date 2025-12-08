import importlib
from typing import Dict, Any


def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class TTSFactory:
    
    provider_to_class = {
        "HuoshanTTS": "src.tts_layer.backends.huoshan_double_streaming_tts.HuoshanTTS",
        "AliyunTTS": "src.tts_layer.backends.aliyun_streaming_tts.AliyunStreamingTTS",
    }

    @classmethod
    def create(cls, provider_name: str, config: Dict[str, Any]) -> Any:

        class_type = cls.provider_to_class.get(provider_name)
        if not class_type:
            raise ValueError(f"Unsupported TTS provider: {provider_name}")
   
        tts_class = load_class(class_type)
        return tts_class(config)
