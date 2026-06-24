import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.TTS)
import websockets
from .base import BaseTTS


class HuoshanTTS(BaseTTS):
    # 固定配置参数
    AUTHORIZATION = "Bearer"
    SPEAKER = "zh_female_qingxinnvsheng_mars_bigtts"
    SPEECH_RATE = 0
    LOUDNESS_RATE = 0
    PITCH = 0
    AUDIO_FORMAT = "pcm"
    SAMPLE_RATE = 16000

    # 各多情感音色支持的 emotion 子集（neutral=通用，不必下发 emotion 字段）
    # 注：下表为占位默认，需以火山控制台「多情感音色」实际支持集为准核对修正。
    VOICE_EMOTIONS = {
        "zh_male_yangguangqingnian_emo_v2_mars_bigtts": {"happy", "sad", "angry", "fear", "surprised"},
        "zh_male_ruyayichen_emo_v2_mars_bigtts": {"happy", "sad", "angry", "fear", "surprised"},
        "zh_female_shuangkuaisisi_emo_v2_mars_bigtts": {"happy", "sad", "angry", "fear", "surprised"},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._forward_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
        self._loop = asyncio.get_event_loop()

        # 只从配置中读取必需参数
        self.appid = str(self.config.get("huoshan_tts_appid", ""))
        self.access_token = self.config.get("huoshan_tts_access_token", "")
        self.resource_id = self.config.get("huoshan_tts_resource_id", "")
        self.ws_url = self.config.get("huoshan_tts_ws_url", "")

        if not (self.appid and self.access_token and self.resource_id and self.ws_url):
            raise ValueError("缺少必要的TTS配置: appid/access_token/resource_id/ws_url")

        # 使用固定参数
        self.authorization = self.AUTHORIZATION
        self.speaker = self.SPEAKER  # 可被 set_voice 覆盖
        self.speech_rate = self.SPEECH_RATE
        self.loudness_rate = self.LOUDNESS_RATE
        self.pitch = self.PITCH
        self.emotion = None          # 由 TTSService 按 appraisal 结果设置
        self.emotion_scale = 4

    # --- Protocol constants ---
    _PROTOCOL_VERSION = 0b0001
    _DEFAULT_HEADER_SIZE = 0b0001
    _FULL_CLIENT_REQUEST = 0b0001
    _AUDIO_ONLY_RESPONSE = 0b1011
    _FULL_SERVER_RESPONSE = 0b1001
    _ERROR_INFORMATION = 0b1111
    _MsgTypeFlagWithEvent = 0b100
    _JSON = 0b0001

    # Session events
    _EVENT_StartSession = 100
    _EVENT_CancelSession = 101
    _EVENT_FinishSession = 102
    _EVENT_SessionStarted = 150
    _EVENT_SessionCanceled = 151
    _EVENT_SessionFinished = 152
    _EVENT_SessionFailed = 153

    # TTS events
    _EVENT_TTSSentenceStart = 350
    _EVENT_TTSSentenceEnd = 351
    _EVENT_TTSResponse = 352
    _EVENT_TaskRequest = 200

    async def _connect(self):
        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }
        connect_kwargs = {
            "max_size": 1000000000,
            "ping_interval": None,
            "ping_timeout": None,
            "close_timeout": 10,
        }
        try:
            try:
                self._ws = await websockets.connect(self.ws_url, additional_headers=headers, **connect_kwargs)
            except TypeError:
                self._ws = await websockets.connect(self.ws_url, extra_headers=headers, **connect_kwargs)
        except Exception as e:
            _log.error(f"TTS 建立连接失败: {e}")
            self._ws = None
            raise
        _log.info(f"TTS 建立连接成功, resource_id={self.resource_id}, speaker={self.speaker}")

    def _header_bytes(self, message_type: int, message_type_specific_flags: int, serial_method: int) -> bytes:
        return bytes([
            (self._PROTOCOL_VERSION << 4) | self._DEFAULT_HEADER_SIZE,
            (message_type << 4) | message_type_specific_flags,
            (serial_method << 4) | 0b0000,  # no compression
            0x00,
        ])

    def _optional_bytes(self, event: int, session_id: Optional[str] = None) -> bytes:
        buf = bytearray()
        buf.extend(int(event).to_bytes(4, "big", signed=True))
        if session_id:
            sid = session_id.encode("utf-8")
            buf.extend(len(sid).to_bytes(4, "big", signed=True))
            buf.extend(sid)
        return bytes(buf)

    def _payload_bytes(self, payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload).encode("utf-8")

    async def _send_event(self, header: bytes, optional: bytes, payload: bytes):
        req = bytearray(header)
        req.extend(optional)
        req.extend(len(payload).to_bytes(4, "big", signed=True))
        req.extend(payload)
        await self._ws.send(req)

    def _supported_emotions(self) -> set:
        return set(self.VOICE_EMOTIONS.get(self.speaker, set()))

    def _resolve_emotion(self):
        """返回 (emotion_or_None, scale)。neutral / 不支持 → None（走通用情感）。"""
        if not self.emotion or self.emotion == "neutral":
            return None, self.emotion_scale
        if self.emotion in self._supported_emotions():
            return self.emotion, self.emotion_scale
        return None, self.emotion_scale  # 降级回落通用

    def _build_req_params(self, text: str = "") -> Dict[str, Any]:
        emotion, scale = self._resolve_emotion()
        audio_params = {
            "format": self.AUDIO_FORMAT,
            "sample_rate": self.SAMPLE_RATE,
            "speech_rate": self.speech_rate,
            "loudness_rate": self.loudness_rate,
        }
        if emotion:
            audio_params["emotion"] = emotion
            audio_params["emotion_scale"] = scale
        return {
            "user": {"uid": "tts_service"},
            "event": 0,
            "namespace": "BidirectionalTTS",
            "req_params": {
                "text": text,
                "speaker": self.speaker,
                "audio_params": audio_params,
                "additions": json.dumps({
                    "post_process": {"pitch": self.pitch}
                })
            }
        }

    def _parse_response(self, msg: bytes) -> Dict[str, Any]:
        if not isinstance(msg, (bytes, bytearray)) or len(msg) < 4:
            return {}

        # 解析header
        header = msg[:4]
        protocol_version = header[0] >> 4 & 0x0F
        header_size = header[0] & 0x0F
        message_type = (header[1] >> 4) & 0x0F
        message_type_specific_flags = header[1] & 0x0F
        serial_method = header[2] >> 4
        compression_type = header[2] & 0x0F
        reserved = header[3]

        result = {
            "protocol_version": protocol_version,
            "header_size": header_size,
            "message_type": message_type,
            "message_type_specific_flags": message_type_specific_flags,
            "serial_method": serial_method,
            "compression_type": compression_type,
            "reserved": reserved,
            "event": 0,
            "session_id": "",
            "payload": b""
        }

        offset = 4

        # 解析optional部分
        if message_type in [self._FULL_SERVER_RESPONSE, self._AUDIO_ONLY_RESPONSE]:
            if message_type_specific_flags == self._MsgTypeFlagWithEvent:
                # 读取event
                if offset + 4 <= len(msg):
                    result["event"] = int.from_bytes(msg[offset:offset+4], "big", signed=True)
                    offset += 4

                # 读取session_id
                if offset + 4 <= len(msg):
                    sid_len = int.from_bytes(msg[offset:offset+4], "big", signed=True)
                    offset += 4
                    if sid_len > 0 and offset + sid_len <= len(msg):
                        result["session_id"] = msg[offset:offset+sid_len].decode("utf-8")
                        offset += sid_len

                # 读取payload
                if offset + 4 <= len(msg):
                    payload_len = int.from_bytes(msg[offset:offset+4], "big", signed=True)
                    offset += 4
                    if payload_len > 0 and offset + payload_len <= len(msg):
                        result["payload"] = msg[offset:offset+payload_len]

        return result

    async def _forward_loop(self):

        session_finished = False
        while self.is_processing and self._ws:
            try:
                msg = await self._ws.recv()
                response = self._parse_response(msg)

                if not response:
                    continue

                event = response["event"]
                message_type = response["message_type"]
                payload = response["payload"]

                if event == self._EVENT_SessionCanceled:
                    session_finished = True
                    break
                elif event == self._EVENT_TTSSentenceStart:
                    if payload:
                        try:
                            json_data = json.loads(payload.decode("utf-8"))
                            self.current_text = json_data.get("text", "")
                        except Exception as e:
                            _log.error(f"解析句子开始事件失败: {e}")
                elif event == self._EVENT_TTSResponse and message_type == self._AUDIO_ONLY_RESPONSE:
                    # 处理音频数据
                    if payload:
                        await self._handle_audio(payload, False)
                elif event == self._EVENT_SessionFinished:
                    session_finished = True
                    break

            except websockets.ConnectionClosed:
                _log.warning("TTS连接已关闭")
                break
            except Exception as e:
                _log.error(f"处理TTS响应错误: {e}")
                break

        if not session_finished:
            await self._ws.close()

        self._forward_task = None

    async def start_session(self, session_id: str) -> bool:
        """启动TTS会话
        当收到SENTENCE_START时，由tts_service调用此方法启动会话
        1.如果当前有未完成的会话，则关闭当前会话，并建立新的连接
        2.发送StartSession请求
        3.启动消息转发循环
        """

        try:
            # 会话开始时检测上个会话的监听状态
            if (
                self._forward_task is not None
                and isinstance(self._forward_task, asyncio.Task)
                and not self._forward_task.done()
            ):
                _log.debug("检测到未完成的上个会话，关闭监听任务和连接...")
                await self.close_ws_forward()
            if not self._ws:
                await self._connect()
                self.is_processing = True
            self._session_id = session_id

            # 启动会话
            header = self._header_bytes(self._FULL_CLIENT_REQUEST, self._MsgTypeFlagWithEvent, self._JSON)
            optional = self._optional_bytes(self._EVENT_StartSession, self._session_id)
            payload = self._payload_bytes(self._build_req_params(text=""))
            await self._send_event(header, optional, payload)

            # 启动消息转发循环
            self._forward_task = asyncio.create_task(self._forward_loop())
            _log.debug(f"TTS会话启动成功")
            return True
        except Exception as e:
            _log.error(f"启动TTS会话失败: {e}")
            await self.close_ws_forward()
            return False

    async def finish_session(self, session_id: str ):
        """结束TTS会话
        当收到SENTENCE_END时，由tts_service调用此方法结束会话，并等待监听任务完成
        1.发送FinishSession请求，但不关闭连接
        2.等待监听任务完成
        """
        try:
            if not self._ws:
                return
            header = self._header_bytes(self._FULL_CLIENT_REQUEST, self._MsgTypeFlagWithEvent, self._JSON)
            optional = self._optional_bytes(self._EVENT_FinishSession, session_id)
            payload = b"{}"
            await self._send_event(header, optional, payload)
            if self._forward_task:
                try:
                    await self._forward_task
                except Exception as e:
                    _log.error(f"等待监听任务完成时发生错误: {e}")
                finally:
                    self._forward_task = None
        except Exception as e:
            _log.error(f"结束会话失败: {e}")

    async def send_text(self, text: str):
        try:
            header = self._header_bytes(self._FULL_CLIENT_REQUEST, self._MsgTypeFlagWithEvent, self._JSON)
            optional = self._optional_bytes(self._EVENT_TaskRequest, self._session_id)
            payload = self._payload_bytes(self._build_req_params(text=text))
            await self._send_event(header, optional, payload)

        except Exception as e:
            _log.error(f"发送文本失败: {e}")

    async def cancel_session(self, session_id: str = None):

        try:
            if not self._ws:
                return

            session_id = session_id or self._session_id
            if not session_id:
                return

            header = self._header_bytes(self._FULL_CLIENT_REQUEST, self._MsgTypeFlagWithEvent, self._JSON)
            optional = self._optional_bytes(self._EVENT_CancelSession, session_id)
            payload = b"{}"
            await self._send_event(header, optional, payload)
        except Exception as e:
            _log.error(f"取消会话失败: {e}")

    async def finish_session(self, session_id: str = None):
        try:
            if not self._ws:
                return

            session_id = session_id or self._session_id


            header = self._header_bytes(self._FULL_CLIENT_REQUEST, self._MsgTypeFlagWithEvent, self._JSON)
            optional = self._optional_bytes(self._EVENT_FinishSession, session_id)
            payload = b"{}"
            await self._send_event(header, optional, payload)
            if self._forward_task:
                try:
                    await self._forward_task
                except Exception as e:
                    _log.error(f"等待监听任务完成时发生错误: {e}")
                finally:
                    self._forward_task = None
        except Exception as e:
            _log.error(f"结束会话失败: {e}")

    def stop_processing(self):
        self.is_processing = False
        if self._forward_task:
            self._forward_task.cancel()
            self._forward_task = None
        if self._ws:
            asyncio.create_task(self._ws.close())
            self._ws = None
        self._session_id = None

    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def close_ws_forward(self):
        await self.close_forward_task()
        await self.close_ws()
        # self._session_id = None
        # self.is_processing = False


    async def close_ws(self):
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None


    async def close_forward_task(self):
          if self._forward_task:
            try:
                self._forward_task.cancel()
                await self._forward_task
            except asyncio.CancelledError:
                pass
            self._forward_task = None


