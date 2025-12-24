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
from typing import Dict, Any, Optional
from loguru import logger

from src.config import WebSocketConfig, AudioConfig, TTSConfig
from src.utils.opus_encoder_utils import OpusCodecUtils
from src.utils.shared_state import SharedState
from src.transport_layer.base import TransportBase


class Handler:
    
    def __init__(self, transport: TransportBase, client_id: str):
        self.transport = transport
        self.client_id = client_id  # 当前客户端ID
        
        # Opus 编解码工具
        self.opus_utils = OpusCodecUtils(
            sample_rate=WebSocketConfig.audio_sample_rate,
            channels=WebSocketConfig.audio_channels,
            frame_size_ms=60,
        )
        
        # 音频流控配置
        self.frame_duration_ms = 60
        
        # 独立服务实例
        self.audio_service = None
        self.agent_service = None
        self.tts_service = None
        
        # 客户端会话状态（单个客户端）
        self.session_id = None
        self.flow_control = {
            "start_time": time.perf_counter(),
            "packet_count": 0,
        }
        self.client_is_speaking = False
        self.is_interrupting = False  # 打断标志，防止打断过程中的重复触发
        
        # 服务任务
        self.agent_process_task = None  # AgentService处理循环任务

        # 统计时延
        self.timing_stats = {
            "user_voice_stop_time": 0.0, # 用户语音停止时间
            "asr_stop_time": 0.0,
            "agent_first_token_time": 0.0,
            "tts_first_chunk_time": 0.0,
            "asr_recognition_latency": 0.0, # ASR识别时延，从用户语音停止到ASR返回最终结果
            "text_response_latency": 0.0, # 文本响应时延，从用户语音停止到系统回复第一个文本
            "audio_response_latency": 0.0, # 音频响应时延，从用户语音停止到系统回复第一个音频包
        }
        
        # 断开时间戳（用于超时清理）
        self._disconnected_at: Optional[float] = None
    
    async def setup_services(self):
        from src.audio_layer.audio_service import AudioService
        from src.agent_layer.agent_service import AgentService
        from src.tts_layer.tts_service import TTSService
        
        # 创建 AudioService
        audio_config = AudioConfig()
        self.audio_service = AudioService(audio_config)
        await self.audio_service.start()
        self.audio_service.set_result_callback(self.asr_result_handler)
        
        # 创建 AgentService
        self.agent_service = AgentService()
        await self.agent_service.start()
        self.agent_service.set_result_callback(self.agent_result_handler)
        
        # 创建 TTSService
        tts_config = TTSConfig()
        self.tts_service = TTSService(tts_config)
        await self.tts_service.start()
        self.tts_service.set_result_callback(self.tts_result_handler)
        
        # 启动 AgentService 的处理循环
        self.agent_process_task = asyncio.create_task(self.agent_service.process())
        
        logger.info(f"handler 创建成功")
    
    async def cleanup_services(self):
        
        # 停止 AgentService 处理循环
        if self.agent_process_task:
            self.agent_process_task.cancel()
            try:
                await self.agent_process_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有服务
        if self.audio_service:
            await self.audio_service.stop()
        if self.agent_service:
            await self.agent_service.stop()
        if self.tts_service:
            await self.tts_service.stop()
        
        # 清理SharedState
        SharedState.remove(f"client_status:{self.client_id}")
        
        logger.info(f"客户端 {self.client_id} 的服务实例已清理")
    
    async def rebind_connection(self):
        logger.info(f"Handler 重新绑定连接: client_id={self.client_id}")
        
        # 如果正在处理中，可能需要清理一些状态
        if self.client_is_speaking:
            logger.warning(f"重连时检测到正在播放，停止播放")
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
            logger.warning(f"发送重连通知失败: {e}")
    
    async def on_message(self, client_id: str, message: Any):
        if client_id != self.client_id:
            return  # 忽略其他客户端的消息
        
        if isinstance(message, bytes):
            # 二进制消息：音频数据
            await self.handle_client_audio_data(message)
        elif isinstance(message, str):
            # 文本消息：JSON 协议消息
            await self.handle_text_message(message)
        else:
            logger.warning(f"收到未知类型的消息: {type(message)}")
    
    async def handle_text_message(self, message: str):
        try:
            data = json.loads(message)
            message_type = data.get('type', '')
            
            if message_type == 'hello':
                await self.handle_hello(data)
            elif message_type == 'timestamp':
                await self.handle_timestamp()
            elif message_type == 'listen':
                await self.handle_listen(data)
            else:
                logger.warning(f"未知消息类型: {message_type}, 消息: {message}")
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 消息失败: {e}, 消息: {message}")
        except Exception as e:
            logger.error(f"处理文本消息失败: {e}, 消息: {message}")
    
    async def handle_hello(self, data: Dict[str, Any]):
        self.session_id = uuid.uuid4().hex
        
        response = {
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "channels": WebSocketConfig.audio_channels,
                "format": "opus",
                "frame_duration": self.frame_duration_ms,
                "sample_rate": WebSocketConfig.audio_sample_rate
            },
            "session_id": self.session_id
        }
        
        await self.transport.send_to_client(self.client_id, json.dumps(response))
        logger.info(f"发送 hello 响应到客户端")

    async def handle_listen(self, data: Dict[str, Any]):
        mode = data.get('mode', '')
        state = data.get('state', '')
        text = data.get('text', '')
        if mode == 'manual' and state == 'detect':
            result = {
                'text': text,
                'is_final': True,
                'timestamp': time.time(),
                'source': 'asr'
            }
            await self.asr_result_handler(result)

    async def handle_timestamp(self):
        self.timing_stats["user_voice_stop_time"] = time.time()

    async def handle_client_audio_data(self, audio_data: bytes):
        # logger.debug(f"收到客户端 {len(audio_data)} 的音频数据")
        if not audio_data:
            return
        
        pcm_data = self.opus_utils.opus_to_pcm(audio_data)
        
        if not pcm_data:
            logger.warning(f"Opus 解码失败，跳过音频数据")
            return
        
        # 直接发送到当前客户端的AudioService
        if self.audio_service:
            await self.audio_service.audio_queue.put(pcm_data)
        else:
            logger.warning("AudioService 未初始化，无法转发音频")
    
    async def asr_result_handler(self, result: Dict[str, Any]):
        """ASR 结果回调处理
        1. 可选：发送 ASR 结果到客户端（用于显示识别文本）
        2. 检测是否存在打断信号：当前处于会话中，且收到新的文本，视为打断
        3. 如果检测到打断，执行打断操作
        4. 将 ASR 结果发送到 Agent 服务队列
        """
        try:
            if not result:
                return
            
            text = result.get('text', '')
            is_final = result.get('is_final', False)
            
            if is_final:
                self.timing_stats["asr_stop_time"] = time.time()
                self.timing_stats["asr_recognition_latency"] = self.timing_stats["asr_stop_time"] - self.timing_stats["user_voice_stop_time"]
                logger.info(f"ASR 识别时延: {self.timing_stats['asr_recognition_latency']}")
            
            if not text:
                return
            
            # 可选：发送 ASR 结果到客户端（用于实时显示识别文本）
            # 如果需要，可以在这里发送 WebSocket 消息给客户端
            
            # 检测打断信号
            should_interrupt = await self.check_interrupt(text, is_final)
            if should_interrupt:
                await self.handle_interrupt()
            
            # 将 ASR 结果发送到 Agent 服务队列
            if self.agent_service and self.agent_service.queue:
                message = {
                    'text': text,
                    'is_final': is_final,
                    'timestamp': result.get('timestamp', time.time()),
                    'source': 'asr'
                }
                await self.agent_service.queue.put(message)
                logger.debug(f"ASR 结果已发送到 Agent 队列: {text} (is_final={is_final})")
            
        except Exception as e:
            logger.error(f"处理 ASR 结果失败: {e}")

    async def agent_result_handler(self, result: Dict[str, Any]):
        """Agent 结果回调处理
        1. 可选：发送 Agent 结果到客户端（用于显示回复文本）
        2. 将 Agent 结果发送到 TTS 服务队列
        """
        try:
            if not result:
                return
            
            text = result.get('text', '')
            if text == "SENTENCE_START":
                self.first_token = True
                self.first_audio_chunk = True
                self.text_buffer = []

            if self.first_token and text != "SENTENCE_START":
                self.timing_stats["agent_first_token_time"] = time.time()
                self.timing_stats["text_response_latency"] = self.timing_stats["agent_first_token_time"] - self.timing_stats["user_voice_stop_time"]
                self.first_token = False
                logger.info(f"文本响应时延: {self.timing_stats['text_response_latency']}")
            
            self.text_buffer.append(text)
            if text == "SENTENCE_END":
                response = " ".join(self.text_buffer[1:-1])
                logger.info(f"文本响应: {response}")


            if not text:
                return
            
            # 可选：发送 Agent 结果到客户端（用于显示回复文本）
            # 如果需要，可以在这里发送 WebSocket 消息给客户端
            
            # 将 Agent 结果发送到 TTS 服务队列
            if self.tts_service and self.tts_service.queue:
                message = {
                    'text': text,
                    'timestamp': result.get('timestamp', time.time()),
                    'source': 'agent'
                }
                await self.tts_service.queue.put(message)
                # logger.debug(f"Agent 结果已发送到 TTS 队列: {text}")
            
        except Exception as e:
            logger.error(f"处理 Agent 结果失败: {e}")

    async def tts_result_handler(self, result: Dict[str, Any]):
        """TTS 结果回调处理
        1. 将 TTS 音频数据转发到客户端
        2. 如果正在打断，忽略音频数据
        """
        try:
            if not result:
                return
            
            # 如果正在执行打断操作，忽略新的音频数据
            if self.is_interrupting:
                logger.debug("正在打断中，忽略TTS音频数据")
                return
            
            # 解析消息
            audio_data = result.get('audio_data', '')
            end_of_stream = result.get('end_of_stream', False)
            if self.first_audio_chunk and audio_data:
                self.timing_stats["audio_response_latency"] = time.time() - self.timing_stats["user_voice_stop_time"]
                logger.info(f"音频响应时延: {self.timing_stats['audio_response_latency']}")
                self.first_audio_chunk = False

            # 状态管理：更新 client_is_speaking
            if audio_data and not self.client_is_speaking:
                # 有音频数据且当前未在播放，标记为开始播放
                self.client_is_speaking = True
                logger.debug(f"客户端 {self.client_id} 开始播放TTS")
            
            if end_of_stream:
                # 流结束，标记为停止播放
                if self.client_is_speaking:
                    self.client_is_speaking = False
                    logger.debug(f"客户端 {self.client_id} 停止播放TTS")
            
            # 如果没有音频数据，跳过播放
            if not audio_data:
                return
            
            await self.send_audio_to_client(audio_data, end_of_stream)
            
        except Exception as e:
            logger.error(f"处理 TTS 结果失败: {e}")

    async def send_audio_to_client(self, audio_data: bytes, end_of_stream: bool):
        """转发音频到客户端（带流控）"""
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
                        #     logger.debug(f"发送音频数据到客户端 {self.client_id}: {len(opus_packet)} bytes")
                        self.flow_control["packet_count"] += 1
                    else:
                        # 发送失败，重置流控状态
                        logger.warning(f"发送音频失败，重置流控状态")
                        self.flow_control["start_time"] = time.perf_counter()
                        self.flow_control["packet_count"] = 0
                        break
                
        except Exception as e:
            logger.error(f"转发音频到客户端 {self.client_id} 失败: {e}")
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
            logger.info(f"检测到打断信号: 系统正在播放TTS，收到新文本: {text[:50]}...")
            return True
        
        # 打断条件2: Agent正在处理中（is_new_session = False）
        # 且收到新的最终ASR结果
        if self.agent_service and not self.agent_service.is_new_session and is_final:
            logger.info(f"检测到打断信号: Agent正在处理中，收到最终文本: {text[:50]}...")
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
            logger.warning("打断操作正在进行中，跳过重复调用")
            return
        
        self.is_interrupting = True
        logger.info(f"开始执行打断操作，客户端: {self.client_id}")
        
        try:
            # 1. 停止TTS会话
            if self.tts_service:
                try:
                    await self.tts_service.end_session()
                except Exception as e:
                    logger.error(f"停止TTS会话失败: {e}")
            
            # 2. 停止Agent会话
            if self.agent_service:
                try:
                    await self.agent_service.end_session()
                except Exception as e:
                    logger.error(f"停止Agent会话失败: {e}")
            
            # 3. 清空队列（避免处理旧数据）
            if self.agent_service and self.agent_service.queue:
                # 清空Agent队列
                while not self.agent_service.queue.empty():
                    try:
                        self.agent_service.queue.get_nowait()
                        self.agent_service.queue.task_done()
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
            
            logger.info(f"打断操作完成，客户端: {self.client_id}")
            
        except Exception as e:
            logger.error(f"执行打断操作时出错: {e}")
        finally:
            self.is_interrupting = False

