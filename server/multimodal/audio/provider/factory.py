from typing import Any, Dict

from server.multimodal.common.importlib_registry import load_class

provider_to_class = {
    "DoubaoStreamingASR": "server.multimodal.audio.provider.doubao_streaming_asr.DoubaoStreamingASR",
    "AliyunStreamingASR": "server.multimodal.audio.provider.aliyun_streaming_asr.AliyunStreamingASR",
    "DashscopeStreamingASR": "server.multimodal.audio.provider.dashscope_streaming_asr.DashscopeStreamingASR",
}

class ASRFactory:

    @classmethod
    def create(cls, provider_name: str, config: Dict[str, Any]) -> Any:

        class_type = provider_to_class.get(provider_name)
        if not class_type:
            raise ValueError(f"Unsupported ASR provider: {provider_name}")
        
        asr_class = load_class(class_type)
        return asr_class(config)

