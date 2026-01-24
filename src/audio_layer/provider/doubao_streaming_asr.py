import json
import gzip
import uuid
import asyncio
import time
import websockets
from typing import Dict, Any, Optional, Callable
from loguru import logger
from .base import BaseASR

logger.disable(__name__)

class DoubaoStreamingASR(BaseASR):
    # 固定配置参数
    WS_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
    CLUSTER = ""
    UID = "streaming_asr_service"
    WORKFLOW = "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate"
    RESULT_TYPE = "single"
    FORMAT = "pcm"
    CODEC = "pcm"
    SAMPLE_RATE = 16000
    LANGUAGE = "zh-CN"
    BITS = 16
    CHANNEL = 1
    AUTH_METHOD = "token"
    SECRET = "access_secret"
    BOOSTING_TABLE_NAME = ""
    CORRECT_TABLE_NAME = ""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.text = ""
        self.max_retries = 3
        self.retry_delay = 2
        self.retry_count = 0
        self.asr_ws = None
        self.forward_task = None
        self.audio_buffer = []
        
        # 只从配置中读取 appid 和 access_token
        self.appid = str(self.config.get("doubao_DOUBAO_STREAMING_ASR_APPID", ""))
        self.access_token = self.config.get("doubao_DOUBAO_STREAMING_ASR_ACCESS_TOKEN", "")
        
        if not self.appid or not self.access_token:
            logger.error("缺少必要的ASR配置参数: appid 和 access_token")
            raise ValueError("ASR配置参数不完整")
        
        # 使用固定参数
        self.cluster = self.CLUSTER
        self.boosting_table_name = self.BOOSTING_TABLE_NAME
        self.correct_table_name = self.CORRECT_TABLE_NAME
        self.ws_url = self.WS_URL
        self.uid = self.UID
        self.workflow = self.WORKFLOW
        self.result_type = self.RESULT_TYPE
        self.format = self.FORMAT
        self.codec = self.CODEC
        self.rate = self.SAMPLE_RATE
        self.language = self.LANGUAGE
        self.bits = self.BITS
        self.channel = self.CHANNEL
        self.auth_method = self.AUTH_METHOD
        self.secret = self.SECRET
        self.start_time = None
    
    async def start_session(self, audio_data: bytes=None) -> bool:
        if self.is_processing:
            logger.warning("ASR服务正在处理中")
            return False
        
        try:
            self.is_processing = True
            headers = self.token_auth() if self.auth_method == "token" else None
            # Create connection with proper headers handling
            connect_kwargs = {
                "max_size": 1000000000,
                "ping_interval": None,
                "ping_timeout": None,
                "close_timeout": 10,
            }
            
            # Handle headers based on websockets version
            if headers:
                try:
                    # Try the newer parameter name first (websockets >= 14.0)
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
            else:
                self.asr_ws = await websockets.connect(
                    self.ws_url,
                    **connect_kwargs
                )
            
            logger.info("ASR WebSocket连接建立完成")
            
            request_params = self.construct_request(str(uuid.uuid4()))
            payload_bytes = str.encode(json.dumps(request_params))
            payload_bytes = gzip.compress(payload_bytes)
            full_client_request = self.generate_header()
            full_client_request.extend((len(payload_bytes)).to_bytes(4, "big"))
            full_client_request.extend(payload_bytes)
            
            logger.info(f"发送初始化请求: {request_params}")
            await self.asr_ws.send(full_client_request)
            
            init_res = await self.asr_ws.recv()
            result = self.parse_response(init_res)
            logger.info(f"收到初始化响应: {result}")
            
            if "code" in result and result["code"] != 1000:
                error_msg = f"ASR服务初始化失败: {result.get('payload_msg', {}).get('error', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            self.forward_task = asyncio.create_task(self._forward_asr_results())
            
            # await self.send_audio_data(audio_data)
            
            
            return True
            
        except Exception as e:
            logger.error(f"建立ASR连接失败: {str(e)}")
            await self.cleanup()
            return False
    
    async def send_audio_data(self, audio_data: bytes):

        if not self.asr_ws or not self.is_processing:
            await self.start_session()

        if self.start_time is None:
            self.start_time = time.time()

        try:
            payload = gzip.compress(audio_data)
            audio_request = bytearray(self.generate_audio_default_header())
            audio_request.extend(len(payload).to_bytes(4, "big"))
            audio_request.extend(payload)
            await self.asr_ws.send(audio_request)
        except Exception as e:
            logger.error(f"发送音频数据失败: {e}")
    
    async def _forward_asr_results(self):
        try:
            while self.is_processing and self.asr_ws:
                response = await self.asr_ws.recv()
                result = self.parse_response(response)
                # if "payload_msg" in result and "result" in result["payload_msg"] and result["payload_msg"]["result"]["text"]:
                    # logger.debug(f"收到ASR结果: {result}")
              
                
                if "payload_msg" in result:
                    payload = result["payload_msg"]
                    
                    if "code" in payload and payload["code"] == 1013:
                        continue
                    
                    if "result" in payload:
                        utterances = payload["result"].get("utterances", [])
                        
                        if (
                            payload.get("audio_info", {}).get("duration", 0) > 2000
                            and not utterances
                            and not payload["result"].get("text")
                        ):
                            logger.error("识别文本：空")
                            self.text = ""
                            break
                        
                        for utterance in utterances:
                            current_text = utterance.get("text", "")
                            is_definite = utterance.get("definite", False)
                            
                            if current_text:
                                self.text = current_text
                                result_data = {
                                    "text": current_text,
                                    "is_final": is_definite,
                                    "timestamp": time.time(),
                                }
                                if is_definite:
                                    await self._handle_result(result_data)
                                    self.stop_processing()
                                    break
                    
                    elif "error" in payload:
                        error_msg = payload.get("error", "未知错误")
                        logger.error(f"ASR服务返回错误: {error_msg}")
                        break
            
        except websockets.ConnectionClosed:
            logger.info("ASR服务连接已关闭")
        except Exception as e:
            logger.error(f"处理ASR结果时发生错误: {str(e)}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        if self.asr_ws:
            try:
                await self.asr_ws.close()
            except Exception as e:
                logger.warning(f"关闭WebSocket连接时出错: {e}")
            self.asr_ws = None
        
        if self.forward_task:
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass
            self.forward_task = None
        
        self.is_processing = False
        self.retry_count = 0
        self.audio_buffer.clear()
    
    def is_connected(self) -> bool:
        return self.asr_ws is not None and not self.asr_ws.closed
    
    def stop_processing(self):
        if self.asr_ws:
            asyncio.create_task(self.asr_ws.close())
            self.asr_ws = None
        self.is_processing = False
    
    def construct_request(self, reqid):
        req = {
            "app": {
                "appid": self.appid,
                "cluster": self.cluster,
                "token": self.access_token,
            },
            "user": {"uid": self.uid},
            "request": {
                "reqid": reqid,
                "workflow": self.workflow,
                "show_utterances": True,
                "result_type": self.result_type,
                "sequence": 1,
                "boosting_table_name": self.boosting_table_name,
                "correct_table_name": self.correct_table_name,
                "end_window_size": 200,
            },
            "audio": {
                "format": self.format,
                "codec": self.codec,
                "rate": self.rate,
                "language": self.language,
                "bits": self.bits,
                "channel": self.channel,
                "sample_rate": self.rate,
            },
        }

        return req
    
    def token_auth(self) -> Dict[str, str]:
        return {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }
    
    def generate_header(
        self,
        version=0x01,
        message_type=0x01,
        message_type_specific_flags=0x00,
        serial_method=0x01,
        compression_type=0x01,
        reserved_data=0x00,
        extension_header: bytes = b"",
    ):
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header
    
    def generate_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x00,
            serial_method=0x01,
            compression_type=0x01,
        )
    
    def parse_response(self, res: bytes) -> Dict[str, Any]:
        if len(res) < 4:
            return {"error": "响应数据长度不足"}
        
        header = res[:4]
        message_type = header[1] >> 4
        
        if message_type == 0x0F:
            code = int.from_bytes(res[4:8], "big", signed=False)
            msg_length = int.from_bytes(res[8:12], "big", signed=False)
            error_msg = json.loads(res[12:].decode("utf-8"))
            return {
                "code": code,
                "msg_length": msg_length,
                "payload_msg": error_msg,
            }
        
        try:
            json_data = res[12:].decode("utf-8")
            result = json.loads(json_data)
            logger.debug(f"成功解析JSON响应: {result}")
            return {"payload_msg": result}
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"解析响应失败: {e}")
            return {"error": f"解析响应失败: {str(e)}"}
