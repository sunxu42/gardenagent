"""百炼 DashScope 流式 TTS（qwen-audio / SpeechSynthesizer v2）。"""

from __future__ import annotations

import asyncio
import re
import threading
from typing import Any

import dashscope
from dashscope.audio.tts_v2 import AudioFormat, ResultCallback, SpeechSynthesizer

from server.multimodal.common.markdown import strip_markdown_for_tts
from shared.observability.logging import LogModule, get_logger

from .base import BaseTTS

_log = get_logger(LogModule.TTS)

_DASHSCOPE_DEFAULT_VOICE = "longanlingxin"
_DEFAULT_MODEL = "qwen-audio-3.0-tts-plus"
_DEFAULT_FORMAT = AudioFormat.PCM_16000HZ_MONO_16BIT
_TEXT_FLUSH_MAX_CHARS = 24
_TEXT_FLUSH_MIN_CHARS = 8
_SENTENCE_END_CHARS = frozenset("。！？\n.!?")
_CLAUSE_END_CHARS = frozenset("，、；,;:")


def _clamp_rate(value: float, *, minimum: float = 0.5, maximum: float = 2.0) -> float:
    return max(minimum, min(maximum, value))


def _map_prosody_rate(raw: int, *, default: float = 1.0, step: float = 0.01) -> float:
    try:
        offset = int(raw)
    except (TypeError, ValueError):
        return default
    return _clamp_rate(default + offset * step)


class _DashscopeTTSCallback(ResultCallback):
    def __init__(self, backend: "DashscopeStreamingTTS") -> None:
        self._backend = backend

    def on_data(self, data: bytes) -> None:
        self._backend._emit_audio(data, False)

    def on_complete(self) -> None:
        self._backend._emit_audio(b"", True)

    def on_error(self, message) -> None:
        _log.error(f"DashScope TTS 合成错误: {message}")
        self._backend._emit_audio(b"", True)

    def on_close(self) -> None:
        self._backend.is_processing = False


def _is_huoshan_voice(voice: str) -> bool:
    """火山引擎音色 ID，不能用于百炼 qwen-audio TTS。"""
    lowered = voice.lower()
    return "mars_bigtts" in lowered or "moon_bigtts" in lowered


class DashscopeStreamingTTS(BaseTTS):
    """基于 dashscope.audio.tts_v2.SpeechSynthesizer 的流式 TTS。"""

    def __init__(self, config: dict[str, Any] | Any = None) -> None:
        super().__init__(config)
        self._api_key = self._read_config("dashscope_api_key", "")
        self._model = self._read_config("tts_model", _DEFAULT_MODEL)
        self._default_voice = self._read_config("tts_voice", "")
        self._websocket_url = self._read_config("tts_websocket_url", "")
        self._language_hints = self._read_language_hints()
        self._audio_format = _DEFAULT_FORMAT

        self._volume = int(self._read_config("tts_volume", 50))
        self.speech_rate = 0
        self.pitch = 0
        self.pitch_rate = 1.0

        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._session_id: str | None = None
        self._synthesizer: SpeechSynthesizer | None = None
        self._session_lock = threading.Lock()
        self._pending_text = ""
        self._audio_queue: asyncio.Queue[tuple[bytes, bool]] | None = None
        self._audio_consumer_task: asyncio.Task[None] | None = None

        if not self._api_key:
            raise ValueError(
                "DashScope TTS 需要在 .env 中配置 DASHSCOPE_API_KEY"
            )

    def _read_config(self, key: str, default: Any) -> Any:
        if self.config is None:
            return default
        if hasattr(self.config, "get"):
            value = self.config.get(key, default)
            if value not in (None, ""):
                return value
        if hasattr(self.config, key):
            value = getattr(self.config, key)
            if value not in (None, ""):
                return value
        return default

    def _read_language_hints(self) -> list[str]:
        raw = None
        if self.config is not None:
            if hasattr(self.config, "tts_language_hints"):
                raw = getattr(self.config, "tts_language_hints")
            elif hasattr(self.config, "get"):
                raw = self.config.get("tts_language_hints")
        if not raw:
            return []
        if isinstance(raw, str):
            return [item.strip() for item in raw.split(",") if item.strip()]
        return [str(item).strip() for item in raw if str(item).strip()]

    def _resolve_voice(self) -> str:
        configured = (self._default_voice or _DASHSCOPE_DEFAULT_VOICE).strip()
        voice = (self.speaker or configured).strip()
        if _is_huoshan_voice(voice):
            fallback = configured if not _is_huoshan_voice(configured) else _DASHSCOPE_DEFAULT_VOICE
            _log.warning(
                f"音色 {voice} 不适用于 DashScope TTS，回退为 {fallback}"
            )
            voice = fallback
        if not voice:
            raise ValueError(
                "DashScope TTS 需要配置音色：在 .config.yaml 的 tts_config.tts_voice "
                "或 data/prompts/soul.yaml 的 voice.type"
            )
        return voice

    def _configure_runtime(self) -> None:
        dashscope.api_key = self._api_key
        if self._websocket_url:
            dashscope.base_websocket_api_url = self._websocket_url

    def _build_synthesizer(self) -> SpeechSynthesizer:
        kwargs: dict[str, Any] = {}
        if self._language_hints:
            kwargs["language_hints"] = self._language_hints
        if self._websocket_url:
            kwargs["url"] = self._websocket_url

        return SpeechSynthesizer(
            model=self._model,
            voice=self._resolve_voice(),
            format=self._audio_format,
            volume=self._volume,
            speech_rate=_map_prosody_rate(self.speech_rate),
            pitch_rate=_map_prosody_rate(self.pitch),
            callback=_DashscopeTTSCallback(self),
            **kwargs,
        )

    def _emit_audio(self, audio_data: bytes, is_final: bool) -> None:
        loop = self._event_loop
        queue = self._audio_queue
        if loop is None or queue is None:
            return
        asyncio.run_coroutine_threadsafe(queue.put((audio_data, is_final)), loop)

    async def _start_audio_consumer(self) -> None:
        await self._stop_audio_consumer()
        self._audio_queue = asyncio.Queue()
        self._audio_consumer_task = asyncio.create_task(
            self._drain_audio_queue(),
            name="dashscope-tts-audio",
        )

    async def _stop_audio_consumer(self) -> None:
        task = self._audio_consumer_task
        self._audio_consumer_task = None
        self._audio_queue = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _drain_audio_queue(self) -> None:
        queue = self._audio_queue
        if queue is None:
            return
        try:
            while True:
                audio_data, is_final = await queue.get()
                await self._handle_audio(audio_data, is_final)
        except asyncio.CancelledError:
            pass

    async def _wait_audio_queue_drained(self, timeout_sec: float = 5.0) -> None:
        queue = self._audio_queue
        if queue is None:
            return
        deadline = asyncio.get_running_loop().time() + timeout_sec
        while asyncio.get_running_loop().time() < deadline:
            if queue.empty():
                await asyncio.sleep(0.02)
                if queue.empty():
                    return
            await asyncio.sleep(0.02)

    def _should_flush_pending_text(self) -> bool:
        buf = self._pending_text
        if not buf:
            return False
        if len(buf) >= _TEXT_FLUSH_MAX_CHARS:
            return True
        last = buf[-1]
        if last in _SENTENCE_END_CHARS:
            return True
        if len(buf) >= _TEXT_FLUSH_MIN_CHARS and last in _CLAUSE_END_CHARS:
            return True
        return False

    async def _flush_pending_text(self, *, force: bool = False) -> None:
        synthesizer = self._synthesizer
        text = self._pending_text
        if not text or synthesizer is None:
            self._pending_text = ""
            return
        if not force and not self._should_flush_pending_text():
            return
        self._pending_text = ""
        try:
            await asyncio.to_thread(synthesizer.streaming_call, text)
        except Exception as exc:
            _log.error(f"发送 DashScope TTS 文本失败: {exc}")

    async def _close_current_session(self) -> None:
        synthesizer = self._synthesizer
        if synthesizer is None:
            return
        self._synthesizer = None
        try:
            await asyncio.to_thread(synthesizer.streaming_cancel)
        except Exception as exc:
            _log.debug(f"关闭 DashScope TTS 会话: {exc}")

    async def start_session(self, session_id: str | None = None) -> bool:
        try:
            await self._close_current_session()
            self._event_loop = asyncio.get_running_loop()
            self._pending_text = ""
            await self._start_audio_consumer()
            self._session_id = session_id
            self._configure_runtime()
            self._synthesizer = self._build_synthesizer()
            self.is_processing = True
            _log.info(
                f"DashScope TTS 会话已准备: model={self._model} voice={self._resolve_voice()}"
            )
            return True
        except Exception as exc:
            _log.error(f"启动 DashScope TTS 会话失败: {exc}")
            self._synthesizer = None
            self.is_processing = False
            await self._stop_audio_consumer()
            return False

    async def send_text(self, text: str) -> None:
        synthesizer = self._synthesizer
        if synthesizer is None:
            _log.warning("DashScope TTS 会话未启动，忽略文本")
            return

        filtered_text = strip_markdown_for_tts(text)
        if not filtered_text:
            return

        self._pending_text += filtered_text
        if self._should_flush_pending_text():
            await self._flush_pending_text()

    async def finish_session(self, session_id: str | None = None) -> None:
        synthesizer = self._synthesizer
        if synthesizer is None:
            await self._stop_audio_consumer()
            return

        self._synthesizer = None
        try:
            await self._flush_pending_text(force=True)
            await asyncio.to_thread(synthesizer.streaming_complete)
            await self._wait_audio_queue_drained()
        except Exception as exc:
            _log.error(f"结束 DashScope TTS 会话失败: {exc}")
        finally:
            self.is_processing = False
            self._session_id = None
            self._pending_text = ""
            await self._stop_audio_consumer()

    async def cancel_session(self, session_id: str | None = None) -> None:
        self._pending_text = ""
        await self._close_current_session()
        self.is_processing = False
        self._session_id = None
        await self._stop_audio_consumer()

    async def cleanup(self) -> None:
        self._pending_text = ""
        await self._close_current_session()
        self.is_processing = False
        self._session_id = None
        await self._stop_audio_consumer()
