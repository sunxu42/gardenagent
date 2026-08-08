"""
业务适配层

负责业务逻辑处理，包括：
- 消息类型解析和路由
- 业务消息处理（hello、协议消息等）
- 音频处理（Opus 编解码、流控）
- 与 ASR/Agent/TTS 服务交互（队列和回调机制）
- 会话管理

每个Handler实例对应一个客户端连接，管理独立的服务实例
使用队列和回调机制连接各个服务：
- ASR 结果 -> Agent 队列 -> Agent 结果 -> TTS 队列 -> TTS 音频 -> 客户端
"""
import asyncio
import json
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from shared.observability.logging import LogModule, bind_session, get_logger
from shared.observability.logging.metrics import TurnMetricsAggregator
from shared.observability.logging.formatting import format_latency_summary
from shared.observability.logging.turn_log import (
    log_agent_response_complete,
    log_llm_ttft,
    log_tts_first_chunk,
    log_user_to_agent,
)
from server.multimodal.audio.opus import OpusCodecUtils
from server.handler.turn_orchestrator import TurnOrchestrator
from server.transport.base import TransportBase


class Handler:

    def __init__(self, config, transport: TransportBase, client_id: str):
        self.config = config
        self.transport = transport
        self.client_id = client_id  # 当前客户端ID

        # Opus 编解码工具
        self.opus_utils = OpusCodecUtils(
            sample_rate=config.audio_config.sample_rate,
            channels=config.audio_config.channels,
            frame_size_ms=60,
        )

        # 音频流控配置
        self.frame_duration_ms = 60

        # 独立服务实例
        self.audio_service = None
        self.session_service = None
        self.tts_service = None

        # 客户端会话状态（单个客户端）
        self.session_id = None
        self.flow_control = {
            "start_time": time.perf_counter(),
            "packet_count": 0,
        }
        self.client_is_speaking = False
        self.is_interrupting = False  # 打断标志，防止打断过程中的重复触发

        # 断开时间戳（用于超时清理）
        self._disconnected_at: Optional[float] = None
        # 输入/输出模态配置
        self.input_modality = config.input_modality
        self.output_modality = config.output_modality
        self.enable_audio_input = "audio" in self.input_modality
        self.enable_audio_output = "audio" in self.output_modality
        self.voice_type_override: Optional[str] = None
        self.client_voice_session_active = False
        self._log = get_logger(LogModule.HANDLER)
        self._metrics = TurnMetricsAggregator(audio_output=self.enable_audio_output)
        self._turns = TurnOrchestrator(
            session_id="",
            client_id=client_id,
            send_json=self.send_json_to_client,
            session_accessor=lambda: self.session_service,
            metrics=self._metrics,
            session_context=self._session_context,
            log=self._log,
        )
        self.text_buffer: List[str] = []
        self.agui_text_buffer: List[str] = []

    @property
    def timing_stats(self) -> dict[str, float | None]:
        return self._turns.timing_stats

    @timing_stats.setter
    def timing_stats(self, value: dict[str, float | None]) -> None:
        self._turns.timing_stats = value

    def _reset_timing_stats(self) -> None:
        self._turns.reset_timing_stats()

    def _try_emit_metrics(self, interrupted: bool = False) -> None:
        payload = self._metrics.finalize(interrupted=interrupted)
        if not payload:
            return
        lat = payload["latency_s"]
        suffix = " (interrupted)" if payload.get("interrupted") else ""
        get_logger(LogModule.METRICS).info(
            format_latency_summary(lat) + suffix,
            latency_s=lat,
            interrupted=payload.get("interrupted", False),
        )

    def _can_send_to_client(self) -> bool:
        return (
            self._disconnected_at is None
            and self.transport.is_client_connected(self.client_id)
        )

    @contextmanager
    def _session_context(self) -> Iterator[None]:
        with bind_session(self.session_id or self.client_id):
            yield

    def _resolve_voice_type(self) -> Optional[str]:
        voice = self.voice_type_override
        if voice and str(voice).strip():
            return str(voice).strip()
        if self.session_service:
            try:
                voice = self.session_service.current_tts_voice()
                if voice and str(voice).strip():
                    return str(voice).strip()
            except Exception as e:
                self._log.debug(f"读取当前音色失败: {e}")
        return None

    def _list_supported_voices(self) -> list[str]:
        voices: list[str] = []
        try:
            backend = getattr(getattr(self, "tts_service", None), "tts_backend", None)
            if backend is None:
                return voices
            speaker = getattr(backend, "speaker", None)
            if isinstance(speaker, str) and speaker.strip():
                voices.append(speaker.strip())
            voice_emotions = getattr(backend, "VOICE_EMOTIONS", None)
            if isinstance(voice_emotions, dict):
                for key in voice_emotions.keys():
                    if isinstance(key, str) and key.strip():
                        voices.append(key.strip())
        except Exception as e:
            self._log.debug(f"读取支持音色列表失败: {e}")
        return list(dict.fromkeys(voices))

    def get_agent_display_name(self) -> str:
        """与 soul.yaml 一致：每次从 prompts YAML 解析当前角色展示名。"""
        try:
            from agent.prompt.persona.soul_profile import resolve_soul_profile

            label = resolve_soul_profile().get("assistant_label")
            if label and str(label).strip():
                return str(label).strip()
        except Exception as e:
            self._log.debug(f"解析 agent 展示名失败，使用默认: {e}")
        return "助手"

    async def send_assistant_to_client(self, data: Dict[str, Any]) -> None:
        if isinstance(data, dict) and data.get("role") == "assistant":
            payload = dict(data)
            payload.setdefault("agent_name", self.get_agent_display_name())
            await self.send_json_to_client(payload)
            return
        await self.send_json_to_client(data)

    async def setup_services(self):
        from server.multimodal.audio.audio_service import AudioService
        from server.multimodal.session.session_service import SessionService
        from server.multimodal.tts.tts_service import TTSService

        # 创建 AudioService（仅在启用语音输入时）
        if self.enable_audio_input:
            self.audio_service = AudioService(self.config.audio_config)
            await self.audio_service.start()
            self.audio_service.set_result_callback(self.asr_result_handler)

        # 创建 SessionService
        self.session_service = SessionService({"agent_type": self.config.agent_type})
        self.session_service.set_result_callback(self.agent_result_handler)
        await self.session_service.start()
        self.session_service.set_appraisal_snapshot_listener(self._on_appraisal_snapshot_ready)

        # 创建 TTSService（仅在启用语音输出时）
        if self.enable_audio_output:
            self.tts_service = TTSService(self.config.tts_config)
            await self.tts_service.start()
            self.tts_service.set_result_callback(self.tts_result_handler)

        self._log.info(f"handler 创建成功")

    async def cleanup_services(self):

        # 停止所有服务
        if self.audio_service:
            await self.audio_service.stop()
        if self.session_service:
            await self.session_service.stop()
        if self.tts_service:
            await self.tts_service.stop()

        self._log.info(f"客户端 {self.client_id} 的服务实例已清理")

    async def rebind_connection(self):
        self._log.info(f"Handler 重新绑定连接: client_id={self.client_id}")

        # 如果正在处理中，可能需要清理一些状态
        if self.client_is_speaking:
            self._log.warning(f"重连时检测到正在播放，停止播放")
            await self.handle_interrupt()

        # 重置流控状态
        self.flow_control["start_time"] = time.perf_counter()
        self.flow_control["packet_count"] = 0

        # 可选：发送重连通知到客户端
        try:
            reconnect_msg = {
                "type": "reconnected",
                "client_id": self.client_id,
                "session_id": self.session_id
            }
            await self.transport.send_to_client(self.client_id, json.dumps(reconnect_msg))
        except Exception as e:
            self._log.warning(f"发送重连通知失败: {e}")

    async def on_message(self, client_id: str, message: Any):
        if client_id != self.client_id:
            return  # 忽略其他客户端的消息

        with bind_session(self.session_id or self.client_id):
            if isinstance(message, bytes):
                await self.handle_client_audio_data(message)
            elif isinstance(message, str):
                await self.handle_json_message(message)
            else:
                self._log.warning(f"收到未知类型的消息: {type(message)}")

    async def handle_json_message(self, message: str):
        try:
            data = json.loads(message)
            channel = data.get("channel")
            if channel == "agui":
                if self.session_service:
                    event = self.session_service.agui_bridge.parse_inbound(data)
                    if event and event.get("type") == "UI_ACTION":
                        self._log.info(f"收到 AG-UI 事件: type={event.get('type')}")
                        await self.session_service.on_ui_action(
                            event,
                            thread_id=self.session_id or self.client_id,
                        )
                return

            # {"role": "user", "content": [{"type": "text", "text": "你好"}]}
            # {"role": "user", "content": [{"type": "audio", "audio": "base64"}]}
            # {"role": "user", "content": [{"type": "image", "image": "base64"}]}
            # {"role": "user", "content": [{"type": "file", "file": "base64"}]}

            role = data.get('role', '')
            msg_type = data.get('type', '')

            if msg_type == 'voice_session':
                await self.handle_voice_session(data)
            elif msg_type == 'affect_lock':
                await self.handle_affect_lock(data)
            elif role == 'hello':
                await self.handle_hello(data)
            elif role == 'user':
                await self.handle_user_message(data)

        except json.JSONDecodeError as e:
            self._log.error(f"解析 JSON 消息失败: {e}, 消息: {message}")
        except Exception as e:
            self._log.error(f"处理文本消息失败: {e}, 消息: {message}")

    async def handle_voice_session(self, data: Dict[str, Any]) -> None:
        """处理前端语音模式开关：{ type: voice_session, state: start|stop }。"""
        state = data.get('state', '')
        incoming_voice = data.get('voice_type')
        if isinstance(incoming_voice, str) and incoming_voice.strip():
            self.voice_type_override = incoming_voice.strip()

        if state == 'start':
            self.client_voice_session_active = True
            if not self.enable_audio_input:
                self._log.warning("语音会话已开启，但 input_modality 未包含 audio，无法识别麦克风输入")
            elif self.audio_service is None:
                self._log.warning("语音会话已开启，但 AudioService 未初始化")
            else:
                self._log.info(f"客户端语音会话已开启: client_id={self.client_id}")
        elif state == 'stop':
            self.client_voice_session_active = False
            self._log.info(f"客户端语音会话已关闭: client_id={self.client_id}")
        else:
            self._log.warning(f"未知 voice_session state: {state!r}")

    async def handle_affect_lock(self, data: Dict[str, Any]) -> None:
        dimension = str(data.get("dimension") or "").strip()
        ref_id = data.get("ref_id")
        if ref_id is not None and not isinstance(ref_id, str):
            ref_id = str(ref_id)
        if not self.session_service:
            await self.send_json_to_client({
                "type": "affect_lock_error",
                "dimension": dimension,
                "message": "emotion service unavailable",
            })
            return
        try:
            state = self.session_service.set_affect_lock(dimension, ref_id)
        except ValueError as e:
            await self.send_json_to_client({
                "type": "affect_lock_error",
                "dimension": dimension,
                "message": str(e),
            })
            return
        payload: Dict[str, Any] = {"type": "affect_lock_state"}
        if isinstance(state, dict):
            payload.update(state)
        await self.send_json_to_client(payload)

    async def handle_hello(self, data: Dict[str, Any]):
        self._turns.reset_session_state()
        if self.session_service:
            self.session_service.clear_affect_locks()
        incoming_voice = data.get("voice_type")
        if isinstance(incoming_voice, str) and incoming_voice.strip():
            self.voice_type_override = incoming_voice.strip()
        self.client_voice_session_active = bool(data.get("voice_session"))
        self.session_id = self.client_id
        self._turns.update_session_id(self.session_id)
        param_version = (
            data.get("param_version")
            or data.get("version")
            or getattr(self.config, "param_version", None)
            or "default"
        )

        response = {
            "type": "hello",
            "version": 1,
            "param_version": param_version,
            "transport": "websocket",
            "audio_params": {
                "channels": self.config.audio_config.channels,
                "format": "opus",
                "frame_duration": self.frame_duration_ms,
                "sample_rate": self.config.audio_config.sample_rate
            },
            "tts": {
                "current_voice": self._resolve_voice_type(),
                "supported_voices": self._list_supported_voices(),
            },
            "emotion": {
                "baseline_vad": self.session_service.baseline_vad() if self.session_service else None,
                "current_vad": (
                    (self.session_service.current_vad_metrics() or {}).get("agent_vad_after")
                    if self.session_service
                    else None
                ),
                "relationship": (
                    self.session_service.current_relationship_snapshot()
                    if self.session_service
                    else None
                ),
                "profile": (
                    self.session_service.emotion_ui_profile()
                    if self.session_service
                    else None
                ),
                "affect_lock": (
                    self.session_service.affect_lock_state()
                    if self.session_service
                    else {"relationship": {"locked": False}, "agent_vad": {"locked": False}}
                ),
            },
            "session_id": self.session_id
        }

        await self.transport.send_to_client(self.client_id, json.dumps(response))
        self._log.info(f"发送 hello 响应到客户端")

    async def handle_timestamp(self):
        self._turns.record_user_voice_stop()

    async def handle_user_message(self, data: Dict[str, Any]):
        incoming_voice = data.get("voice_type")
        if isinstance(incoming_voice, str) and incoming_voice.strip():
            self.voice_type_override = incoming_voice.strip()

        text = ""
        content_list = data.get('content', [])
        for content in content_list:
            if content.get('type', '') == 'text':
                text += content.get('text', '')

        agui_meta = data.get("agui")
        if self.session_service:
            await self.session_service.finalize_pending_agui_turn()
            if isinstance(agui_meta, dict):
                message_id = agui_meta.get("messageId")
                run_id = agui_meta.get("runId")
                if (
                    isinstance(message_id, str)
                    and message_id.strip()
                    and isinstance(run_id, str)
                    and run_id.strip()
                ):
                    self.session_service.begin_agui_turn(
                        message_id=message_id.strip(),
                        run_id=run_id.strip(),
                    )
                else:
                    self.session_service.clear_agui_turn()
            else:
                self.session_service.clear_agui_turn()

        result = {
            "text": text,
            "is_final": True,
            "timestamp": time.time(),
            "source": "text",
        }
        await self.asr_result_handler(result)

    def _on_appraisal_snapshot_ready(self, digest: str) -> None:
        self._turns.on_appraisal_snapshot_ready(digest)

    async def _emit_settled_for_next_turn(self) -> None:
        await self._turns.emit_settled_for_next_turn()

    async def handle_client_audio_data(self, audio_data: bytes):
        if not self.client_voice_session_active:
            return
        # 如果未启用语音输入，直接丢弃音频数据
        if not self.enable_audio_input:
            self._log.debug("当前配置未启用语音输入，忽略收到的音频数据")
            return
        # self._log.debug(f"收到客户端 {len(audio_data)} 的音频数据")
        if not audio_data:
            return

        pcm_data = self.opus_utils.opus_to_pcm(audio_data)

        if not pcm_data:
            self._log.warning(f"Opus 解码失败，跳过音频数据")
            return

        # 直接发送到当前客户端的AudioService
        if self.audio_service:
            await self.audio_service.audio_queue.put(pcm_data)
        else:
            self._log.warning("AudioService 未初始化，无法转发音频")

    async def asr_result_handler(self, result: Dict[str, Any]):
        """ASR 结果回调处理
        1. 可选：发送 ASR 结果到客户端（用于显示识别文本）
        2. 检测是否存在打断信号：当前处于会话中，且收到新的文本，视为打断
        3. 如果检测到打断，执行打断操作
        4. 将 ASR 结果发送到 Agent 服务队列
        """
        with self._session_context():
            await self._asr_result_handler_impl(result)

    async def _asr_result_handler_impl(self, result: Dict[str, Any]):
        try:
            if not result:
                return

            text = result.get('text', '')
            is_final = result.get('is_final', False)

            if not is_final and text and text.strip():
                self._turns.record_asr_partial()

            if is_final:
                self._turns.begin_final_turn(text)

            if not text:
                return

            source = str(result.get("source") or "asr").strip() or "asr"
            # Text chat enables AG-UI in handle_user_message; do not clear it here.
            if self.session_service and source != "text":
                self.session_service.clear_agui_turn()

            await self.send_json_to_client({
                "role": "user",
                "content": text,
                "is_final": is_final,
                "source": source,
            })

            # 检测打断信号
            should_interrupt = await self.check_interrupt(text, is_final)
            if should_interrupt:
                await self.handle_interrupt()

            # 将 ASR 结果发送到 Agent 服务队列
            if is_final and text.strip() and self.session_service and self.session_service.queue:
                turn_id = self._turns.current_turn_id()
                asr_sec = self._turns.asr_latency_sec()
                log_user_to_agent(text=text, source=source, asr_sec=asr_sec if asr_sec > 0 else None)
                message = {
                    'text': text,
                    'is_final': is_final,
                    'timestamp': result.get('timestamp', time.time()),
                    'source': source,
                    'thread_id': self.session_id or self.client_id,
                    'turn_id': turn_id,
                }
                await self.session_service.queue.put(message)

        except Exception as e:
            self._log.error(f"处理 ASR 结果失败: {e}")

    async def agent_result_handler(self, result: Dict[str, Any]):
        """Agent 结果回调处理
        1. 可选：发送 Agent 结果到客户端（用于显示回复文本）
        2. 将 Agent 结果发送到 TTS 服务队列
        """
        with self._session_context():
            await self._agent_result_handler_impl(result)

    async def _pause_asr_during_reply(self) -> None:
        """Agent 开始播报时关闭 ASR，避免空闲连接在 TTS 期间超时。"""
        audio_service = self.audio_service
        if audio_service is None:
            return
        asr = getattr(audio_service, "asr_service", None)
        if asr is None:
            return
        stop = getattr(asr, "stop_processing", None)
        if callable(stop):
            stop()

    async def _agent_result_handler_impl(self, result: Dict[str, Any]):
        try:
            if not result:
                return

            msg_type = result.get('msg_type', '')
            if msg_type == "agui":
                envelope = result.get("envelope")
                if isinstance(envelope, dict):
                    event = envelope.get("event")
                    if isinstance(event, dict) and event.get("type") == "TEXT_MESSAGE_CONTENT":
                        delta = event.get("delta")
                        if isinstance(delta, str) and delta:
                            self.agui_text_buffer.append(delta)
                    await self.send_json_to_client(envelope)
                return

            use_agui = bool(self.session_service and self.session_service.use_agui_channel)

            if msg_type == "SENTENCE_START":
                self.first_token = True
                self.first_audio_chunk = True
                self.text_buffer = []
                self.agui_text_buffer = []
                text = "SENTENCE_START"
                if self.client_voice_session_active:
                    await self._pause_asr_during_reply()
                if not use_agui:
                    await self.send_assistant_to_client({"role": "assistant", "content": "SENTENCE_START"})
            elif msg_type == "SENTENCE_END":
                text = "SENTENCE_END"
                if not use_agui:
                    await self.send_assistant_to_client({"role": "assistant", "content": "SENTENCE_END"})
                reply_text = "".join(
                    chunk
                    for chunk in (self.agui_text_buffer or self.text_buffer)
                    if isinstance(chunk, str)
                )
                log_agent_response_complete(text=reply_text)
                self._metrics.mark_sentence_end()
                self._try_emit_metrics()
                await self._emit_settled_for_next_turn()
            elif msg_type == "response":
                response = result.get('response', '')
                if self.first_token:
                    ttft_sec = self._turns.mark_agent_first_token()
                    log_llm_ttft(ttft_sec)
                    self._metrics.mark_llm_ttft(ttft_sec)
                    self.first_token = False

                if isinstance(response, dict) and response.get("role") == "assistant":
                    if not use_agui:
                        await self.send_assistant_to_client(response)
                else:
                    if not use_agui:
                        await self.send_json_to_client(response)

                text = response.get('content', '') if isinstance(response, dict) else ''
                self.text_buffer.append(text)

            # 将 Agent 结果发送到 TTS 服务队列（仅语音会话且启用语音输出时）
            if (
                self.client_voice_session_active
                and self.enable_audio_output
                and self.tts_service
                and self.tts_service.queue
            ):

                message = {
                    'text': text,
                    'timestamp': result.get('timestamp', time.time()),
                    'source': 'agent'
                }
                # SENTENCE_START 时附带当前情绪与角色音色（本轮快照），驱动情感化 TTS
                if text == "SENTENCE_START" and self.session_service:
                    try:
                        voice = self._resolve_voice_type()
                        emotion, scale = self.session_service.current_tts_emotion()
                        prosody = self.session_service.current_tts_prosody()
                        if len(prosody) >= 3:
                            speech_rate, pitch, loudness_rate = prosody
                        else:
                            speech_rate, pitch = prosody[0], prosody[1]
                            loudness_rate = 0
                        if voice:
                            message['voice_type'] = voice
                        if emotion:
                            message['emotion'] = emotion
                        message['emotion_scale'] = scale
                        message['speech_rate'] = speech_rate
                        message['pitch'] = pitch
                        message['loudness_rate'] = loudness_rate
                    except Exception as e:
                        self._log.debug(f"获取 TTS 情感/音色失败: {e}")

                await self.tts_service.queue.put(message)
                # self._log.debug(f"Agent 结果已发送到 TTS 队列: {text}")

        except Exception as e:
            self._log.error(f"处理 Agent 结果失败: {e}")

    async def send_json_to_client(self, data: Dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError("data 必须是字典类型")
        if not self._can_send_to_client():
            return
        await self.transport.send_to_client(self.client_id, json.dumps(data))

    async def tts_result_handler(self, result: Dict[str, Any]):
        """TTS 结果回调处理
        1. 将 TTS 音频数据转发到客户端
        2. 如果正在打断，忽略音频数据
        """
        with self._session_context():
            await self._tts_result_handler_impl(result)

    async def _tts_result_handler_impl(self, result: Dict[str, Any]):
        try:
            if not result:
                return

            # 如果正在执行打断操作，忽略新的音频数据
            if self.is_interrupting:
                return

            # 解析消息
            audio_data = result.get('audio_data', '')
            end_of_stream = result.get('end_of_stream', False)
            if self.first_audio_chunk and audio_data:
                self.flow_control["start_time"] = time.perf_counter()
                self.flow_control["packet_count"] = 0
                tts_sec, audio_e2e_sec = self._turns.mark_tts_first_chunk()
                if tts_sec > 0:
                    log_tts_first_chunk(tts_sec)
                    self._metrics.mark_tts_first_chunk(tts_sec)
                if audio_e2e_sec > 0:
                    self._metrics.mark_audio_e2e(audio_e2e_sec)
                self._try_emit_metrics()
                self.first_audio_chunk = False

            # 状态管理：更新 client_is_speaking
            if audio_data and not self.client_is_speaking:
                self.client_is_speaking = True

            if end_of_stream:
                if self.client_is_speaking:
                    self.client_is_speaking = False

            # 如果没有音频数据，跳过播放
            if not audio_data:
                return

            await self.send_audio_to_client(audio_data, end_of_stream)

        except Exception as e:
            self._log.error(f"处理 TTS 结果失败: {e}")

    async def send_audio_to_client(self, audio_data: bytes, end_of_stream: bool):
        """转发音频到客户端（带流控）"""
        if not self._can_send_to_client():
            return
        try:
            # 将 PCM 编码为 Opus 流
            opus_packets = self.opus_utils.pcm_to_opus_stream(audio_data, end_of_stream)

            # 发送每个 Opus 包（带流控）
            for opus_packet in opus_packets:
                if opus_packet:
                    # 计算期望发送时间
                    expected_time = self.flow_control["start_time"] + (
                        self.flow_control["packet_count"] * self.frame_duration_ms / 1000
                    )
                    current_time = time.perf_counter()
                    delay = expected_time - current_time

                    # 流控：如果还没到发送时间，等待
                    if delay > 0:
                        await asyncio.sleep(delay)
                    else:
                        # 如果已经晚了，调整起始时间
                        self.flow_control["start_time"] += abs(delay)

                    # 发送音频包
                    success = await self.transport.send_to_client(self.client_id, opus_packet)
                    if success:
                        # if self.flow_control["packet_count"] % 50 == 0:
                        #     self._log.debug(f"发送音频数据到客户端 {self.client_id}: {len(opus_packet)} bytes")
                        self.flow_control["packet_count"] += 1
                    else:
                        # 发送失败，重置流控状态
                        self._log.warning(f"发送音频失败，重置流控状态")
                        self.flow_control["start_time"] = time.perf_counter()
                        self.flow_control["packet_count"] = 0
                        break

        except Exception as e:
            self._log.error(f"转发音频到客户端 {self.client_id} 失败: {e}")
            # 重置流控状态
            self.flow_control["start_time"] = time.perf_counter()
            self.flow_control["packet_count"] = 0

    async def check_interrupt(self, text: str, is_final: bool = False) -> bool:
        """检测是否需要打断

        Args:
            text: ASR识别的文本
            is_final: 是否为最终结果

        Returns:
            bool: 如果需要打断返回True，否则返回False
        """
        # 如果正在执行打断操作，不再重复检测
        if self.is_interrupting:
            return False

        # 如果文本为空，不需要打断
        if not text or not text.strip():
            return False

        # 打断条件1: 系统正在播放TTS音频（client_is_speaking = True）
        # 且收到新的ASR文本（无论是中间结果还是最终结果）
        if self.client_is_speaking:
            self._log.info(f"检测到打断信号: 系统正在播放TTS，收到新文本: {text[:50]}...")
            return True

        # 打断条件2: Agent正在处理中（is_new_session = False）
        # 且收到新的最终ASR结果
        if self.session_service and not self.session_service.is_new_session and is_final:
            self._log.info(f"检测到打断信号: Agent正在处理中，收到最终文本: {text[:50]}...")
            return True

        return False

    async def handle_interrupt(self):
        """执行打断操作
        1. 停止当前TTS播放
        2. 停止当前Agent处理
        3. 清空相关队列
        4. 重置状态
        """
        if self.is_interrupting:
            self._log.warning("打断操作正在进行中，跳过重复调用")
            return

        self.is_interrupting = True
        self._log.info(f"开始执行打断操作，客户端: {self.client_id}")

        try:
            # 1. 停止TTS会话
            if self.tts_service:
                try:
                    await self.tts_service.end_session()
                except Exception as e:
                    self._log.error(f"停止TTS会话失败: {e}")

            # 2. 停止Agent会话
            if self.session_service:
                try:
                    await self.session_service.end_session()
                except Exception as e:
                    self._log.error(f"停止Agent会话失败: {e}")

            # 3. 清空队列（避免处理旧数据）
            if self.session_service and self.session_service.queue:
                # 清空Agent队列
                while not self.session_service.queue.empty():
                    try:
                        self.session_service.queue.get_nowait()
                        self.session_service.queue.task_done()
                    except asyncio.QueueEmpty:
                        break

            if self.tts_service and self.tts_service.queue:
                # 清空TTS队列
                while not self.tts_service.queue.empty():
                    try:
                        self.tts_service.queue.get_nowait()
                        self.tts_service.queue.task_done()
                    except asyncio.QueueEmpty:
                        break

            # 4. 重置状态
            self.client_is_speaking = False
            # 重置流控状态
            self.flow_control["start_time"] = time.perf_counter()
            self.flow_control["packet_count"] = 0

            self._log.info(f"打断操作完成，客户端: {self.client_id}")

        except Exception as e:
            self._log.error(f"执行打断操作时出错: {e}")
        finally:
            self._try_emit_metrics(interrupted=True)
            self.is_interrupting = False

