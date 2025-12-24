"""
业务适配层
- 客户端文本输入 -> Agent 队列 -> Agent 结果 -> 客户端文本输出
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from loguru import logger

from src.utils.shared_state import SharedState
from src.transport_layer.base import TransportBase


class Handler:
    
    def __init__(self, transport: TransportBase, client_id: str):
        self.transport = transport
        self.client_id = client_id  # 当前客户端ID
        self.agent_service = None
        self.session_id = None
        self.is_interrupting = False  # 打断标志，防止打断过程中的重复触发
        self.agent_process_task = None  # AgentService处理循环任务
        self.first_token = False
        self.text_buffer = []
        
        # 断开时间戳（用于超时清理）
        self._disconnected_at: Optional[float] = None
    
    async def setup_services(self):
        from src.agent_layer.agent_service import AgentService
        self.agent_service = AgentService()
        await self.agent_service.start()
        self.agent_service.set_result_callback(self.agent_result_handler)
        self.agent_process_task = asyncio.create_task(self.agent_service.process())
        
        logger.info(f"handler 创建成功")
    
    async def cleanup_services(self):
        if self.agent_process_task:
            self.agent_process_task.cancel()
            try:
                await self.agent_process_task
            except asyncio.CancelledError:
                pass
        
        if self.agent_service:
            await self.agent_service.stop()
        
        SharedState.remove(f"client_status:{self.client_id}")
        
        logger.info(f"客户端 {self.client_id} 的服务实例已清理")
    
    async def rebind_connection(self):
        logger.info(f"Handler 重新绑定连接: client_id={self.client_id}")
        
        # 重置状态
        self.text_buffer = []
        self.first_token = False
        
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
        
        if isinstance(message, str):
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
                ## 临时处理，后续修改
                await self.handle_llm_format_text(data)
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
            "session_id": self.session_id
        }
        
        await self.transport.send_to_client(self.client_id, json.dumps(response))
        logger.info(f"发送 hello 响应到客户端")

    async def handle_llm_format_text(self, data: Dict[str, Any]):
        text = data.get('content', '')
        if self.agent_service and self.agent_service.queue:
            message = {
                'text': text,
                'is_final': True,
                'timestamp': time.time(),
                'source': 'user'
            }
            await self.agent_service.queue.put(message)
            logger.debug(f"用户文本已发送到 Agent 队列: {text}")
    async def handle_listen(self, data: Dict[str, Any]):
        mode = data.get('mode', '')
        state = data.get('state', '')
        text = data.get('text', '')
        
        if mode == 'manual' and state == 'detect' and text:
            # 检测打断信号
            should_interrupt = await self.check_interrupt(text)
            if should_interrupt:
                await self.handle_interrupt()
            
            # 将文本发送到 Agent 服务队列
            if self.agent_service and self.agent_service.queue:
                message = {
                    'text': text,
                    'is_final': True,
                    'timestamp': time.time(),
                    'source': 'user'
                }
                await self.agent_service.queue.put(message)
                logger.debug(f"用户文本已发送到 Agent 队列: {text}")

    async def handle_timestamp(self):
        """处理时间戳消息（保留用于兼容性）"""
        pass
    

    async def agent_result_handler(self, result: Dict[str, Any]):
 
            if not result:
                return
            text = result.get('text', '')

            await self.send_text_to_client(result.get('text', ''))
            
            if text=="SENTENCE_START":
                self.text_buffer = []
            if text and text not in ["SENTENCE_START", "SENTENCE_END"]:
                self.text_buffer.append(text)
            if text == "SENTENCE_END":
                response_text = "".join(self.text_buffer)
                logger.info(f"文本响应: {response_text}")          

    async def send_text_to_client(self, text: str):
        try:
            response = {
                "type": "text_response",
                "text": text,
                "timestamp": time.time()
            }
            await self.transport.send_to_client(self.client_id, json.dumps(response))
        except Exception as e:
            logger.error(f"发送文本响应到客户端失败: {e}")
    
    async def check_interrupt(self, text: str) -> bool:
        """检测是否需要打断
        
        Args:
            text: 用户输入的文本
            
        Returns:
            bool: 如果需要打断返回True，否则返回False
        """
        # 如果正在执行打断操作，不再重复检测
        if self.is_interrupting:
            return False
        
        # 如果文本为空，不需要打断
        if not text or not text.strip():
            return False
        
        # 打断条件: Agent正在处理中（is_new_session = False）
        if self.agent_service and not self.agent_service.is_new_session:
            logger.info(f"检测到打断信号: Agent正在处理中，收到新文本: {text[:50]}...")
            return True
        
        return False

    async def handle_interrupt(self):
        """执行打断操作
        1. 停止当前Agent处理
        2. 清空相关队列
        3. 重置状态
        """
        if self.is_interrupting:
            logger.warning("打断操作正在进行中，跳过重复调用")
            return
        
        self.is_interrupting = True
        logger.info(f"开始执行打断操作，客户端: {self.client_id}")
        
        try:
            # 1. 停止Agent会话
            if self.agent_service:
                try:
                    await self.agent_service.end_session()
                except Exception as e:
                    logger.error(f"停止Agent会话失败: {e}")
            
            # 2. 清空队列（避免处理旧数据）
            if self.agent_service and self.agent_service.queue:
                # 清空Agent队列
                while not self.agent_service.queue.empty():
                    try:
                        self.agent_service.queue.get_nowait()
                        self.agent_service.queue.task_done()
                    except asyncio.QueueEmpty:
                        break
            
            # 3. 重置状态
            self.text_buffer = []
            self.first_token = False
            
            logger.info(f"打断操作完成，客户端: {self.client_id}")
            
        except Exception as e:
            logger.error(f"执行打断操作时出错: {e}")
        finally:
            self.is_interrupting = False

