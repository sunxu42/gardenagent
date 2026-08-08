"""百炼 DashScope 实时语音识别（Fun-ASR / Qwen ASR）。"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult

from shared.observability.logging import LogModule, get_logger

from .base import BaseASR

_log = get_logger(LogModule.ASR)

_DEFAULT_MODEL = "fun-asr-realtime-2026-02-28"
_DEFAULT_FORMAT = "pcm"
_DEFAULT_SAMPLE_RATE = 16000
_DEFAULT_LANGUAGE_HINTS = ("zh", "en")
# 百炼实时 ASR 约 23s 无活动会超时；提前主动结束会话，避免 CLIENT_ERROR 噪音。
_ASR_IDLE_TIMEOUT_SEC = 15.0


def _format_recognition_error(result: RecognitionResult) -> str:
    """Format ASR errors without calling RecognitionResult.__str__ (SDK bug on errors)."""
    parts: list[str] = []
    code = getattr(result, "code", None)
    message = getattr(result, "message", None)
    request_id = getattr(result, "request_id", None)
    if code:
        parts.append(f"code={code}")
    if message:
        parts.append(str(message))
    if request_id:
        parts.append(f"request_id={request_id}")
    if parts:
        return "; ".join(parts)

    try:
        sentence = result.get_sentence()
        if isinstance(sentence, dict):
            text = sentence.get("text") or sentence.get("message")
            if text:
                return str(text).strip()
    except Exception:
        pass
    return "unknown DashScope ASR error"


class _DashscopeASRCallback(RecognitionCallback):
    def __init__(self, asr: DashscopeStreamingASR) -> None:
        self._asr = asr

    def on_open(self) -> None:
        self._asr._mark_session_ready()

    def on_event(self, result: RecognitionResult) -> None:
        self._asr._handle_recognition_event(result)

    def on_error(self, result: RecognitionResult) -> None:
        self._asr._handle_recognition_error(result)

    def on_close(self) -> None:
        self._asr._mark_session_closed()


class DashscopeStreamingASR(BaseASR):
    """基于 dashscope.audio.asr.Recognition 的流式 ASR。"""

    def __init__(self, config: dict[str, Any] | Any = None) -> None:
        super().__init__(config)
        self.text = ""
        self.server_ready = False
        self.audio_buffer: list[bytes] = []

        self._api_key = self._read_config("dashscope_api_key", "")
        self._model = self._read_config("asr_model", _DEFAULT_MODEL)
        self._format = self._read_config("asr_format", _DEFAULT_FORMAT)
        self._sample_rate = int(self._read_config("sample_rate", _DEFAULT_SAMPLE_RATE))
        self._language_hints = self._read_language_hints()

        self._recognition: Recognition | None = None
        self._callback: _DashscopeASRCallback | None = None
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._stop_lock = threading.Lock()
        self._last_audio_at: float = 0.0
        self._idle_watch_task: asyncio.Task[None] | None = None

        if not self._api_key:
            raise ValueError(
                "DashScope ASR 需要在 .env 中配置 DASHSCOPE_API_KEY"
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
            if hasattr(self.config, "asr_language_hints"):
                raw = getattr(self.config, "asr_language_hints")
            elif hasattr(self.config, "get"):
                raw = self.config.get("asr_language_hints")
        if not raw:
            return list(_DEFAULT_LANGUAGE_HINTS)
        if isinstance(raw, str):
            return [item.strip() for item in raw.split(",") if item.strip()]
        return [str(item).strip() for item in raw if str(item).strip()]

    def _configure_api_key(self) -> None:
        dashscope.api_key = self._api_key

    def _mark_session_ready(self) -> None:
        self.server_ready = True
        recognition = self._recognition
        if recognition is None:
            return
        for chunk in self.audio_buffer:
            try:
                recognition.send_audio_frame(chunk)
            except Exception as exc:
                _log.warning(f"发送缓存音频失败: {exc}")
                break
        self.audio_buffer.clear()

    def _mark_session_closed(self) -> None:
        self.server_ready = False
        self.is_processing = False

    def _emit_result(self, text: str, is_final: bool) -> None:
        if not self._event_loop:
            return
        payload = {
            "text": text,
            "is_final": is_final,
            "timestamp": time.time(),
        }
        asyncio.run_coroutine_threadsafe(
            self._handle_result(payload),
            self._event_loop,
        )

    def _handle_recognition_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if not isinstance(sentence, dict):
            return

        text = str(sentence.get("text") or "").strip()
        if not text:
            return

        is_final = RecognitionResult.is_sentence_end(sentence)
        self.text = text
        self._emit_result(text, is_final)
        if is_final:
            self._schedule_session_stop()

    def _handle_recognition_error(self, result: RecognitionResult) -> None:
        message = _format_recognition_error(result)
        if "timeout" in message.lower():
            _log.warning(f"DashScope ASR 会话超时结束: {message}")
        else:
            _log.error(f"DashScope ASR 识别错误: {message}")
        self._schedule_session_stop()

    async def _start_idle_watch(self) -> None:
        await self._stop_idle_watch()
        self._last_audio_at = time.monotonic()
        self._idle_watch_task = asyncio.create_task(
            self._idle_watch_loop(),
            name="dashscope-asr-idle-watch",
        )

    async def _stop_idle_watch(self) -> None:
        task = self._idle_watch_task
        self._idle_watch_task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _idle_watch_loop(self) -> None:
        try:
            while self.is_processing:
                await asyncio.sleep(1.0)
                if not self.is_processing:
                    break
                idle_sec = time.monotonic() - self._last_audio_at
                if idle_sec >= _ASR_IDLE_TIMEOUT_SEC:
                    _log.debug(
                        f"DashScope ASR 空闲 {idle_sec:.0f}s，主动结束会话"
                    )
                    self._schedule_session_stop()
                    break
        except asyncio.CancelledError:
            pass

    def _schedule_idle_watch_stop(self) -> None:
        loop = self._event_loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._stop_idle_watch(), loop)

    def _reset_session_state(self) -> None:
        self._recognition = None
        self._callback = None
        self.server_ready = False
        self.is_processing = False
        self.audio_buffer.clear()

    def _schedule_session_stop(self) -> None:
        self._schedule_idle_watch_stop()
        if self._recognition is None:
            self._reset_session_state()
            return
        # 先标记本地状态，避免 stop 线程完成前继续往已关闭会话写音频。
        self.is_processing = False
        self.server_ready = False

        def _stop() -> None:
            with self._stop_lock:
                recognition = self._recognition
                if recognition is None:
                    self._reset_session_state()
                    return
                try:
                    recognition.stop()
                except Exception as exc:
                    if "has stopped" not in str(exc).lower():
                        _log.warning(f"停止 DashScope ASR 会话: {exc}")
                finally:
                    self._reset_session_state()

        threading.Thread(target=_stop, daemon=True).start()

    async def start_session(self, audio_data: bytes | None = None) -> bool:
        if self.is_processing:
            _log.warning("ASR 服务正在处理中")
            return False

        try:
            self._event_loop = asyncio.get_running_loop()
            self._configure_api_key()
            self.audio_buffer.clear()
            self.server_ready = False

            callback = _DashscopeASRCallback(self)
            recognition_kwargs: dict[str, Any] = {}
            if self._language_hints:
                recognition_kwargs["language_hints"] = self._language_hints

            recognition = Recognition(
                model=self._model,
                callback=callback,
                format=self._format,
                sample_rate=self._sample_rate,
                **recognition_kwargs,
            )
            self._callback = callback
            self._recognition = recognition
            recognition.start()

            self.is_processing = True
            await self._start_idle_watch()
            if audio_data:
                if self.server_ready:
                    recognition.send_audio_frame(audio_data)
                else:
                    self.audio_buffer.append(audio_data)

            _log.info(
                f"DashScope ASR 会话已启动: model={self._model} "
                f"format={self._format} sample_rate={self._sample_rate}"
            )
            return True
        except Exception as exc:
            _log.error(f"建立 DashScope ASR 连接失败: {exc}")
            await self._stop_idle_watch()
            await self.cleanup()
            return False

    async def send_audio_data(self, audio_data: bytes) -> None:
        if not audio_data:
            return

        self._last_audio_at = time.monotonic()

        if not self.is_processing or self._recognition is None:
            success = await self.start_session(audio_data)
            if not success:
                return
            return

        recognition = self._recognition
        if recognition is None:
            return

        if not self.server_ready:
            self.audio_buffer.append(audio_data)
            return

        try:
            await asyncio.to_thread(recognition.send_audio_frame, audio_data)
        except Exception as exc:
            message = str(exc)
            if "has stopped" in message.lower():
                _log.debug("DashScope ASR 会话已结束，下一帧将重新建连")
                self._reset_session_state()
                await self._stop_idle_watch()
                if await self.start_session(audio_data):
                    return
                return
            _log.error(f"发送音频数据失败: {exc}")
            await self.cleanup()

    def stop_processing(self) -> None:
        self._schedule_session_stop()

    def is_connected(self) -> bool:
        return self.is_processing and self._recognition is not None

    async def cleanup(self) -> None:
        await self._stop_idle_watch()
        self._schedule_session_stop()
        self.text = ""
        await super().cleanup()
