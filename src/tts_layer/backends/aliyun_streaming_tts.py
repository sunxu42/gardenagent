from re import A
import uuid
import json
import hmac
import hashlib
import base64
import time
import asyncio
import websockets
from typing import Dict, Any, Optional
from datetime import datetime
from urllib import parse
from loguru import logger
from .base import BaseTTS
import requests

def clean_markdown(text: str) -> str:
    # 移除常见的markdown标记
    import re
    # 移除粗体、斜体、代码块等
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 粗体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # 斜体
    text = re.sub(r'`([^`]+)`', r'\1', text)  # 行内代码
    text = re.sub(r'```[\s\S]*?```', '', text)  # 代码块
    text = re.sub(r'#+\s*', '', text)  # 标题
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 链接
    return text.strip()

class AccessToken:
    
    @staticmethod
    def _encode_text(text):
        encoded_text = parse.quote_plus(text)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _encode_dict(dic):
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def create_token(access_key_id, access_key_secret):
        parameters = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid1()),
            "SignatureVersion": "1.0",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Version": "2019-02-28",
        }

        query_string = AccessToken._encode_dict(parameters)
        string_to_sign = (
            "GET"
            + "&"
            + AccessToken._encode_text("/")
            + "&"
            + AccessToken._encode_text(query_string)
        )

        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        signature = AccessToken._encode_text(signature)

        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (
            signature,
            query_string,
        )

        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            key = "Token"
            if key in root_obj:
                token = root_obj[key]["Id"]
                expire_time = root_obj[key]["ExpireTime"]
                return token, expire_time
        return None, None


class AliyunStreamingTTS(BaseTTS):
    
    # 固定配置参数
    VOICE = "longxiaochun"
    FORMAT = "pcm"
    SAMPLE_RATE = 16000
    VOLUME = 50
    SPEECH_RATE = 0
    PITCH_RATE = 0
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 基础配置
        self.access_key_id = self.config.get("aliyun_access_key_id", "")
        self.access_key_secret = self.config.get("aliyun_access_key_secret", "")
        self.appkey = self.config.get("aliyun_appkey", "")
        
        # 使用固定参数
        self.format = self.FORMAT
        self.sample_rate = self.SAMPLE_RATE
        self.voice = self.VOICE
        self.volume = self.VOLUME
        self.speech_rate = self.SPEECH_RATE
        self.pitch_rate = self.PITCH_RATE
        
        # WebSocket配置
        self.host = self.config.get("aliyun_host", "nls-gateway-cn-beijing.aliyuncs.com")
        if "-internal." in self.host:
            self.ws_url = f"ws://{self.host}/ws/v1"
        else:
            self.ws_url = f"wss://{self.host}/ws/v1"
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self.last_active_time: Optional[float] = None
        self.message_id: str = ""
        self._session_id: Optional[str] = None
        
        # Token管理
        if self.access_key_id and self.access_key_secret:
            self._refresh_token()
        else:
            self.token = self.config.get("aliyun_token", "")
            self.expire_time = None
            
        if not self.token:
            raise ValueError("无法获取有效的访问Token，请提供 access_key_id/access_key_secret 或 token")
        self._server_ready = False


    def _refresh_token(self):
        if self.access_key_id and self.access_key_secret:
            self.token, expire_time_str = AccessToken.create_token(
                self.access_key_id, self.access_key_secret
            )
            if not expire_time_str:
                raise ValueError("无法获取有效的Token过期时间")

            expire_str = str(expire_time_str).strip()
            try:
                if expire_str.isdigit():
                    expire_time = datetime.fromtimestamp(int(expire_str))
                else:
                    expire_time = datetime.strptime(expire_str, "%Y-%m-%dT%H:%M:%SZ")
                self.expire_time = expire_time.timestamp() - 60  # 提前60秒刷新
            except Exception as e:
                raise ValueError(f"无效的过期时间格式: {expire_str}") from e
        else:
            self.expire_time = None

        if not self.token:
            raise ValueError("无法获取有效的访问Token")

    def _is_token_expired(self):
        """检查Token是否过期"""
        if not self.expire_time:
            return False
        return time.time() > self.expire_time

    async def _ensure_connection(self):
        """确保WebSocket连接可用"""
        try:
            if self._is_token_expired():
                logger.warning("Token已过期，正在自动刷新...")
                self._refresh_token()
            
            current_time = time.time()
            if self.ws and current_time - self.last_active_time < 10:
                # 10秒内可以复用连接
                return self.ws
            
            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers={"X-NLS-Token": self.token},
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )
            self.last_active_time = time.time()
            return self.ws
        except Exception as e:
            logger.error(f"建立连接失败: {str(e)}")
            self.ws = None
            self.last_active_time = None
            raise

    async def start_session(self, session_id: str = None) -> bool:
        try:
            # 检测上个会话的监听状态
            if (
                self._monitor_task is not None
                and isinstance(self._monitor_task, asyncio.Task)
                and not self._monitor_task.done()
            ):
                logger.info("检测到未完成的上个会话，关闭监听任务和连接...")
                await self.cleanup()

            # 建立新连接
            await self._ensure_connection()
            self._server_ready = False
            self.is_processing = True
            self._session_id = session_id
            self.message_id = str(uuid.uuid4().hex)

            # 启动监听任务
            self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

            # 发送StartSynthesis请求
            start_request = {
                "header": {
                    "message_id": self.message_id,
                    "task_id": self._session_id,
                    "namespace": "FlowingSpeechSynthesizer",
                    "name": "StartSynthesis",
                    "appkey": self.appkey,
                },
                "payload": {
                    "voice": self.voice,
                    "format": self.format,
                    "sample_rate": self.sample_rate,
                    "volume": self.volume,
                    "speech_rate": self.speech_rate,
                    "pitch_rate": self.pitch_rate,
                    "enable_subtitle": True,
                },
            }
            await self.ws.send(json.dumps(start_request))
            self.last_active_time = time.time()
            logger.debug(f"TTS会话启动成功: {self._session_id}")
            return True
        except Exception as e:
            logger.error(f"启动TTS会话失败: {e}")
            await self.cleanup()
            return False

    async def finish_session(self, session_id: str):
        try:
            if not self.ws:
                return


            stop_request = {
                "header": {
                    "message_id": self.message_id,
                    "task_id": session_id,
                    "namespace": "FlowingSpeechSynthesizer",
                    "name": "StopSynthesis",
                    "appkey": self.appkey,
                }
            }
            await self.ws.send(json.dumps(stop_request))
            self.last_active_time = time.time()
            
            # 等待监听任务完成
            if self._monitor_task:
                try:
                    await self._monitor_task
                except Exception as e:
                    logger.error(f"等待监听任务完成时发生错误: {str(e)}")
                finally:
                    self._monitor_task = None
            
        except Exception as e:
            logger.error(f"结束会话失败: {str(e)}")
            await self.cleanup()
            raise

    async def send_text(self, text: str):
        if not self.ws:
            logger.warning("WebSocket连接不存在或未在处理，无法发送文本")
            return
                # 等待服务器准备好（收到SynthesisStarted事件）
        if not self._server_ready:
            max_wait = 5.0  # 最多等待5秒
            wait_interval = 0.1
            waited = 0.0
            while not self._server_ready and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            if not self._server_ready:
                logger.error("等待服务器准备就绪超时")
                return
        try:
            # 简单的文本清理（移除markdown标记）
            filtered_text = clean_markdown(text)
            # 阿里云要求 RunSynthesis 必须携带非空文本，过滤掉空请求
            if not filtered_text.strip():
                logger.warning(
                    f"Aliyun TTS 过滤掉空文本请求，不发送到服务端。原始文本: {repr(text)}"
                )
                return
            run_request = {
                "header": {
                    "message_id": self.message_id,
                    "task_id": self._session_id,
                    "namespace": "FlowingSpeechSynthesizer",
                    "name": "RunSynthesis",
                    "appkey": self.appkey,
                },
                "payload": {"text": filtered_text},
            }
            await self.ws.send(json.dumps(run_request))
            self.last_active_time = time.time()
        except Exception as e:
            logger.error(f"发送TTS文本失败: {str(e)}")

    async def _start_monitor_tts_response(self):
        session_finished = False
        try:
            while self.is_processing:
                try:
                    msg = await self.ws.recv()
                    self.last_active_time = time.time()
                    
                    if isinstance(msg, str):  # 文本控制消息
                        try:
                            data = json.loads(msg)
                            header = data.get("header", {})
                            event_name = header.get("name")
                            if event_name == "SynthesisStarted":
                                self._server_ready = True
                                logger.debug(f"会话开始, session_id: {self._session_id}")

                            elif event_name == "SentenceBegin":
                                logger.debug(f"句子生成开始")

                            elif event_name == "SentenceEnd":
                                logger.debug(f"句子生成结束")

                            elif event_name == "SynthesisCompleted":
                                logger.debug(f"会话结束, session_id: {self._session_id}")
                                session_finished = True
                                break

                            elif event_name == "TaskFailed":
                                # 任务失败，记录详细信息并结束本次会话
                                payload_data = data.get("payload") or {}
                                error_code = payload_data.get("error_code") or payload_data.get("code", "unknown")
                                error_message = payload_data.get("error_message") or payload_data.get("message", "未知错误")
                                logger.error(
                                    f"Aliyun TTS TaskFailed: code={error_code}, "
                                    f"message={error_message}, raw={data}"
                                )
                                session_finished = True
                                break


                        except json.JSONDecodeError:
                            logger.warning(f"收到无效的JSON消息: {msg}")
                    
                    elif isinstance(msg, (bytes, bytearray)):  # 二进制消息（音频数据）
                        await self._handle_audio(msg, False)
                        
                except websockets.ConnectionClosed:
                    logger.warning("WebSocket连接已关闭")
                    break
                except Exception as e:
                    logger.error(f"处理TTS响应时出错: {e}")
                    break
            
            # 仅在连接异常时才关闭
            if not session_finished:
                await self.close_ws()

        finally:
            # 重置状态，允许启动新会话（无论本次会话是正常结束还是异常结束）
            self._monitor_task = None
            self.is_processing = False

    async def cleanup(self):
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"关闭时取消监听任务错误: {e}")
            self._monitor_task = None

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            self.last_active_time = None
        
        self._session_id = None
        self.is_processing = False


    async def close_ws_forward(self):
        await self.close_forward_task()
        await self.close_ws()


    async def close_ws(self):
        if self.ws: 
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None


    async def close_forward_task(self):
          if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None


