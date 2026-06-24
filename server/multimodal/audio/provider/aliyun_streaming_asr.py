import json
import time
import uuid
import hmac
import base64
import hashlib
import asyncio
import requests
import websockets
import random
from typing import Dict, Any, Optional
from urllib import parse
from datetime import datetime
from shared.observability.logging import LogModule, get_logger
from .base import BaseASR

_log = get_logger(LogModule.ASR)

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
            "GET" + "&" + AccessToken._encode_text("/") + "&" + AccessToken._encode_text(query_string)
        )
        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        signature = AccessToken._encode_text(signature)
        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (signature, query_string)
        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            if "Token" in root_obj:
                return root_obj["Token"]["Id"], root_obj["Token"]["ExpireTime"]
        return None, None


class AliyunStreamingASR(BaseASR):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.text = ""
        self.asr_ws = None
        self.forward_task = None
        self.server_ready = False
        self.audio_buffer = []
        
        # 基础配置
        self.access_key_id = config.get("aliyun_ACCESS_KEY_ID", "") if config else ""
        self.access_key_secret = config.get("aliyun_ACCESS_KEY_SECRET", "") if config else ""
        self.appkey = config.get("aliyun_APPKEY", "") if config else ""
        self.token = config.get("aliyun_TOKEN", "") if config else ""
        self.host = config.get("aliyun_HOST", "nls-gateway-cn-shanghai.aliyuncs.com") if config else "nls-gateway-cn-shanghai.aliyuncs.com"
        
        # 如果配置的是内网地址（包含-internal.aliyuncs.com），则使用ws协议，默认是wss协议
        if "-internal." in self.host:
            self.ws_url = f"ws://{self.host}/ws/v1"
        else:
            self.ws_url = f"wss://{self.host}/ws/v1"
        
        self.max_sentence_silence = config.get("aliyun_MAX_SENTENCE_SILENCE", 8000) if config else 8000
        self.expire_time = None
        
        # Token管理
        if self.access_key_id and self.access_key_secret:
            self._refresh_token()
        elif not self.token:
            raise ValueError("必须提供 access_key_id+access_key_secret 或者直接提供 token")
        
        if not self.appkey:
            raise ValueError("必须提供 appkey")
    
    def _refresh_token(self):
        self.token, expire_time_str = AccessToken.create_token(self.access_key_id, self.access_key_secret)
        if not self.token:
            raise ValueError("无法获取有效的访问Token")
        
        try:
            expire_str = str(expire_time_str).strip()
            if expire_str.isdigit():
                expire_time = datetime.fromtimestamp(int(expire_str))
            else:
                expire_time = datetime.strptime(expire_str, "%Y-%m-%dT%H:%M:%SZ")
            self.expire_time = expire_time.timestamp() - 60
        except Exception as e:
            _log.warning(f"解析 token 过期时间失败: {e}")
            self.expire_time = None
    
    def _is_token_expired(self):
        return self.expire_time and time.time() > self.expire_time
    
    async def start_session(self, audio_data: bytes = None) -> bool:
        if self.is_processing:
            _log.warning("ASR服务正在处理中")
            return False
        
        try:
            # 检查并刷新Token
            if self._is_token_expired():
                self._refresh_token()
            
            # 建立WebSocket连接
            headers = {"X-NLS-Token": self.token}
            connect_kwargs = {
                "max_size": 1000000000,
                "ping_interval": None,
                "ping_timeout": None,
                "close_timeout": 5,
            }
            
            # 处理不同版本的 websockets 库
            try:
                self.asr_ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=headers,
                    **connect_kwargs
                )
            except TypeError:
                # Fall back to older parameter name (websockets < 14.0)
                self.asr_ws = await websockets.connect(
                    self.ws_url,
                    extra_headers=headers,
                    **connect_kwargs
                )
            
            _log.info("ASR WebSocket连接建立完成")
            
            self.is_processing = True
            self.server_ready = False
            
            # 启动结果转发任务
            self.forward_task = asyncio.create_task(self._forward_asr_results())
            
            # 发送开始请求
            start_request = {
                "header": {
                    "namespace": "SpeechTranscriber",
                    "name": "StartTranscription",
                    "status": 20000000,
                    "message_id": ''.join(random.choices('0123456789abcdef', k=32)),
                    "task_id": ''.join(random.choices('0123456789abcdef', k=32)),
                    "status_text": "Gateway:SUCCESS:Success.",
                    "appkey": self.appkey
                },
                "payload": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "enable_intermediate_result": True,
                    "enable_punctuation_prediction": True,
                    "enable_inverse_text_normalization": True,
                    "max_sentence_silence": self.max_sentence_silence,
                    "enable_voice_detection": False,
                }
            }
            await self.asr_ws.send(json.dumps(start_request, ensure_ascii=False))
            _log.info("已发送开始请求，等待服务器准备...")
            
            # 如果有初始音频数据，缓存它
            if audio_data:
                self.audio_buffer.append(audio_data)
            
            return True
            
        except Exception as e:
            _log.error(f"建立ASR连接失败: {str(e)}")
            await self.cleanup()
            return False
    
    async def send_audio_data(self, audio_data: bytes):
        if not self.asr_ws or not self.is_processing:
            # 如果未开始会话，先启动会话
            success = await self.start_session(audio_data)
            if not success:
                return
        
        # 如果服务器还未准备好，缓存音频数据
        if not self.server_ready:
            self.audio_buffer.append(audio_data)
            return
        
        try:
            await self.asr_ws.send(audio_data)
        except Exception as e:
            _log.error(f"发送音频数据失败: {e}")
            await self.cleanup()
    
    async def _forward_asr_results(self):

        try:
            while self.is_processing and self.asr_ws:
                try:
                    response = await asyncio.wait_for(self.asr_ws.recv(), timeout=1.0)
                    result = json.loads(response)
                    header = result.get("header", {})
                    payload = result.get("payload", {})
                    message_name = header.get("name", "")
                    status = header.get("status", 0)
                    
                    if status != 20000000:
                        if status in [40000004, 40010004]:  # 连接超时或客户端断开
                            _log.warning(f"连接问题，状态码: {status}")
                            break
                        elif status in [40270002, 40270003]:  # 音频问题
                            _log.warning(f"音频处理问题，状态码: {status}")
                            continue
                        else:
                            _log.error(f"识别错误，状态码: {status}, 消息: {header.get('status_text', '')}")
                            continue
                    
                    # 收到TranscriptionStarted表示服务器准备好接收音频数据
                    if message_name == "TranscriptionStarted":
                        self.server_ready = True
                        _log.info("服务器已准备，开始发送缓存音频...")
                        
                        # 发送缓存音频
                        for cached_audio in self.audio_buffer:
                            try:
                                await self.asr_ws.send(cached_audio)
                            except Exception as e:
                                _log.warning(f"发送缓存音频失败: {e}")
                                break
                        
                        self.audio_buffer.clear()
                        continue
                    
                    # 处理识别结果
                    if message_name == "TranscriptionResultChanged":
                        # 中间结果
                        text = payload.get("result", "")
                        if text:
                            self.text = text
                            result_data = {
                                "text": text,
                                "is_final": False,
                                "timestamp": time.time(),
                            }
                            await self._handle_result(result_data)
                    
                    elif message_name == "SentenceEnd":
                        # 最终结果
                        text = payload.get("result", "")
                        if text:
                            self.text = text
                            result_data = {
                                "text": text,
                                "is_final": True,
                                "timestamp": time.time(),
                            }
                            await self._handle_result(result_data)
                            self.stop_processing()
                            break
                    
                    elif message_name == "TranscriptionCompleted":
                        # 识别完成
                        _log.info("识别完成")
                        self.stop_processing()
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    _log.info("ASR服务连接已关闭")
                    break
                except Exception as e:
                    _log.error(f"处理结果失败: {str(e)}")
                    break
                    
        except Exception as e:
            _log.error(f"结果转发失败: {str(e)}")
        finally:
            await self.cleanup()
    
    def stop_processing(self):
        if self.asr_ws and self.is_processing:
            asyncio.create_task(self._send_stop_request())
        self.is_processing = False
    
    async def _send_stop_request(self):
        if not self.asr_ws:
            return
        
        try:
            stop_msg = {
                "header": {
                    "namespace": "SpeechTranscriber",
                    "name": "StopTranscription",
                    "status": 20000000,
                    "message_id": ''.join(random.choices('0123456789abcdef', k=32)),
                    "status_text": "Client:Stop",
                    "appkey": self.appkey
                }
            }
            _log.info("正在发送ASR终止请求")
            await self.asr_ws.send(json.dumps(stop_msg, ensure_ascii=False))
            await asyncio.sleep(0.1)
            _log.info("ASR终止请求已发送")
        except Exception as e:
            _log.error(f"ASR终止请求发送失败: {e}")
    
    def is_connected(self) -> bool:
        return self.asr_ws is not None and not self.asr_ws.closed
    
    async def cleanup(self):
        _log.info(f"开始ASR会话清理 | 当前状态: processing={self.is_processing}, server_ready={self.server_ready}")
        
        if self.asr_ws and (self.is_processing or self.server_ready):
            await self._send_stop_request()
        
        self.is_processing = False
        self.server_ready = False
        _log.info("ASR状态已重置")
        
        if self.forward_task and not self.forward_task.done():
            self.forward_task.cancel()
            try:
                await asyncio.wait_for(self.forward_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            finally:
                self.forward_task = None
        
        if self.asr_ws:
            try:
                _log.debug("正在关闭WebSocket连接")
                await asyncio.wait_for(self.asr_ws.close(), timeout=2.0)
                _log.debug("WebSocket连接已关闭")
            except Exception as e:
                _log.error(f"关闭WebSocket连接失败: {e}")
            finally:
                self.asr_ws = None
        
        self.audio_buffer.clear()
        self.text = ""
        
        _log.info("ASR会话清理完成")
        
        await super().cleanup()
