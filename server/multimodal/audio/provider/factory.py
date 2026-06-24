import importlib
from typing import Dict, Any, Optional

provider_to_class = {
    "DoubaoStreamingASR": "server.multimodal.audio.provider.doubao_streaming_asr.DoubaoStreamingASR",
    "AliyunStreamingASR": "server.multimodal.audio.provider.aliyun_streaming_asr.AliyunStreamingASR",
}

def load_class(class_type):
    module_path, class_name = class_type.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class ASRFactory:

    @classmethod
    def create(cls, provider_name: str, config: Dict[str, Any]) -> Any:

        class_type = provider_to_class.get(provider_name)
        if not class_type:
            raise ValueError(f"Unsupported ASR provider: {provider_name}")
        
        asr_class = load_class(class_type)
        return asr_class(config)

