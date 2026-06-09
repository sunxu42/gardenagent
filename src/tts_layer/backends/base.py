from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional


class BaseTTS(ABC):
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_processing = False
        self.audio_callback: Optional[Callable[[bytes, bool], None]] = None
        self.speaker: str = ""
        self.emotion: Optional[str] = None
        self.emotion_scale: int = 4
    
    def set_audio_callback(self, callback: Callable[[bytes, bool], None]):
        self.audio_callback = callback

    def set_voice(self, voice_type: str) -> None:
        if voice_type:
            self.speaker = voice_type

    def set_emotion(self, emotion: Optional[str], emotion_scale: int = 4) -> None:
        self.emotion = (emotion or "").strip().lower() or None
        self.emotion_scale = max(1, min(5, int(emotion_scale)))

    def set_prosody(self, speech_rate: int = 0, pitch: int = 0) -> None:
        if hasattr(self, "speech_rate"):
            self.speech_rate = int(speech_rate)
        if hasattr(self, "pitch"):
            self.pitch = int(pitch)
        if hasattr(self, "pitch_rate"):
            self.pitch_rate = int(pitch)
    
    @abstractmethod
    async def start_session(self, session_id: str = None) -> bool:
        """Start TTS session. Returns True if started."""
        pass
    
    @abstractmethod
    async def send_text(self, text: str):
        """Send additional text during an active session (if supported)."""
        pass
    
  
    @abstractmethod
    async def finish_session(self, session_id: str):
        """Finish TTS session. Returns True if finished."""
        pass

    
    async def _handle_audio(self, audio_data: Optional[bytes], is_final: bool = False):
        if self.audio_callback:
            await self.audio_callback(audio_data or b"", is_final)
            
    


