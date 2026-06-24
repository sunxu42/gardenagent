from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import asyncio

from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.ASR)


class BaseASR(ABC):
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_processing = False
        self.result_callback = None
    
    @abstractmethod
    async def start_session(self, audio_data: bytes) -> bool:
        pass
    
    @abstractmethod
    async def send_audio_data(self, audio_data: bytes):
        pass
    
  
    async def stop_processing(self):
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        pass
    
    def set_result_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.result_callback = callback
    
    async def _handle_result(self, result: Dict[str, Any]):
        if self.result_callback:
            try:
                await self.result_callback(result)
            except Exception as e:
                _log.error(f"处理结果回调失败: {e}")
    
    async def cleanup(self):
        self.is_processing = False
