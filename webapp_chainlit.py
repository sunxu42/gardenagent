"""
基于 Chainlit 的 Web 应用
使用 Chainlit 框架提供更好的聊天界面，同时保持与现有 WebSocket 后端的兼容性
"""

import asyncio
import json
import os
import time
import uuid
from typing import Optional

import chainlit as cl
import websockets
from loguru import logger


def get_ws_url() -> str:
    """获取 WebSocket 服务器地址"""
    host = os.getenv("WEBSOCKET_HOST", "localhost")
    port = os.getenv("WEBSOCKET_PORT", "8005")
    scheme = "ws"
    return f"{scheme}://{host}:{port}"


class WebSocketManager:
    """管理 WebSocket 连接的类"""
    
    def __init__(self, client_id: str = "chainlit_client"):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.client_id = client_id
        self._connected = False
    
    async def connect(self):
        """建立 WebSocket 连接（只连接一次）"""
        if self._connected and self.websocket is not None:
            # 检查连接是否真的活跃
            try:
                if hasattr(self.websocket, "closed"):
                    is_closed = self.websocket.closed
                    if not is_closed:
                        logger.debug(f"WebSocket 已连接，复用现有连接: client_id={self.client_id}")
                        return self.websocket
                    else:
                        logger.debug(f"检测到连接已关闭，准备重新连接: client_id={self.client_id}")
                else:
                    # 如果没有 closed 属性，假设连接是活跃的
                    logger.debug(f"WebSocket 已连接（无 closed 属性），复用现有连接: client_id={self.client_id}")
                    return self.websocket
            except Exception as e:
                logger.debug(f"检查连接状态时出错: {e}，准备重新连接")
            # 如果检查失败，重置状态
            self._connected = False
            self.websocket = None
        
        # 真正创建新连接
        logger.info(f"正在创建新的 WebSocket 连接: client_id={self.client_id}")
        try:
            self.websocket = await websockets.connect(
                get_ws_url(),
                additional_headers={
                    "client-id": self.client_id
                },
                ping_interval=20,  # 每20秒发送一次ping
                ping_timeout=10   # ping超时时间
            )
            self._connected = True
            logger.info(f"✅ 已连接到 WebSocket 服务器: {get_ws_url()}, client_id={self.client_id}")
            return self.websocket
        except Exception as e:
            self._connected = False
            logger.error(f"连接 WebSocket 失败: {e}")
            raise
    
    async def disconnect(self):
        """断开 WebSocket 连接"""
        self._connected = False
        if self.websocket is not None:
            try:
                await self.websocket.close()
            except Exception:
                pass
            finally:
                self.websocket = None
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._connected:
            logger.debug(f"is_connected: _connected=False, client_id={self.client_id}")
            return False
        if self.websocket is None:
            logger.debug(f"is_connected: websocket=None, client_id={self.client_id}")
            return False
        try:
            # 直接访问 closed 属性，如果不存在会抛出 AttributeError
            # 如果 closed 属性存在，检查是否为 False（未关闭）
            if hasattr(self.websocket, "closed"):
                is_closed = self.websocket.closed
                result = not is_closed
                logger.debug(f"is_connected: closed={is_closed}, result={result}, client_id={self.client_id}")
                return result
            # 如果没有 closed 属性，假设连接是活跃的（因为 _connected=True）
            logger.debug(f"is_connected: 无 closed 属性，返回 True, client_id={self.client_id}")
            return True
        except Exception as e:
            logger.debug(f"检查连接状态时出错: {e}, client_id={self.client_id}")
            # 出错时，如果 _connected=True，假设连接是活跃的
            return self._connected
    
    async def send_message(self, message: str) -> None:
        """发送消息到 WebSocket 服务器"""
        if not self.is_connected():
            # 尝试重新连接
            logger.warning(f"连接已断开，尝试重新连接: client_id={self.client_id}")
            await self.connect()
        else:
            logger.debug(f"使用现有连接发送消息: client_id={self.client_id}")
        
        try:
            await self.websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            self._connected = False
            raise ConnectionError("WebSocket 连接已关闭")
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self._connected = False
            raise
    
    async def receive_stream(self):
        """接收流式响应（异步生成器）"""
        # 不在这里检查连接，因为 send_message 已经确保连接了
        # 如果连接真的断开，会在 recv() 时抛出异常
        logger.debug(f"开始接收流式响应: client_id={self.client_id}, _connected={self._connected}")
        
        if self.websocket is None:
            raise ConnectionError("WebSocket 未初始化")
        
        while True:
            try:
                data = await self.websocket.recv()
                
                # 处理字节数据
                if isinstance(data, bytes):
                    try:
                        data = data.decode("utf-8")
                    except Exception:
                        continue
                
                if not isinstance(data, str):
                    continue
                
                # 解析 JSON
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                
                # 只处理 text_response 类型的消息
                if obj.get("type") != "text_response":
                    continue
                
                piece = obj.get("text", "")
                
                # 跳过特殊标记和空内容
                if not piece or piece == "SENTENCE_START":
                    continue
                
                if piece == "SENTENCE_END":
                    break
                
                yield piece
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket 连接已关闭")
                self._connected = False
                break
            except Exception as e:
                logger.error(f"接收消息时出错: {e}")
                self._connected = False
                break


@cl.on_chat_start
async def on_chat_start():
    """聊天会话开始时调用"""
    # 为每个会话创建独立的 WebSocket 管理器
    ws_manager = WebSocketManager()
    cl.user_session.set("ws_manager", ws_manager)
    
    await cl.Message(
        content="欢迎使用 GardenAgent！我已经准备好回答你的问题。",
        author="System"
    ).send()
    
    # 建立 WebSocket 连接（只连接一次）
    try:
        await ws_manager.connect()
    except Exception as e:
        await cl.Message(
            content=f"⚠️ 无法连接到后端服务器: {e}\n请确保 WebSocket 服务器正在运行。",
            author="System"
        ).send()


@cl.on_chat_end
async def on_chat_end():
    """聊天会话结束时调用"""
    ws_manager = cl.user_session.get("ws_manager")
    if ws_manager:
        await ws_manager.disconnect()
        logger.info("聊天会话结束，已断开 WebSocket 连接")


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息"""
    # 从会话中获取 WebSocket 管理器
    ws_manager = cl.user_session.get("ws_manager")
    if not ws_manager:
        await cl.Message(
            content="❌ WebSocket 连接未初始化，请刷新页面重试。",
            author="System"
        ).send()
        return
    
    user_input = message.content
    
    # 构建发送给后端的消息格式
    query_message = {
        "type": "llm",
        "role": "user",
        "content": user_input
    }
    
    payload = json.dumps(query_message, ensure_ascii=False)
    
    # 创建响应消息对象用于流式更新
    response_msg = cl.Message(content="", author="Assistant")
    await response_msg.send()
    
    # 记录开始时间
    start_time = time.time()
    first_token_received = False
    full_response = ""
    
    try:
        # 确保连接正常（send_message 内部会处理重连）
        # 发送消息到 WebSocket 服务器
        await ws_manager.send_message(payload)
        
        # 接收并流式显示响应
        async for piece in ws_manager.receive_stream():
            if piece:
                full_response += piece
                
                # 更新消息内容
                response_msg.content = full_response
                await response_msg.update()
                
                # 记录首次令牌时间
                if not first_token_received:
                    elapsed = time.time() - start_time
                    logger.info(f"首次令牌延迟: {elapsed:.2f} 秒")
                    first_token_received = True
        
        # 如果没有任何响应，显示错误信息
        if not full_response:
            response_msg.content = "⚠️ 未收到服务器响应，请检查后端服务是否正常运行。"
            await response_msg.update()
        else:
            total_time = time.time() - start_time
            logger.info(f"完整响应时间: {total_time:.2f} 秒")
    
    except ConnectionError as e:
        error_msg = f"❌ 连接错误: {str(e)}"
        logger.error(error_msg)
        response_msg.content = error_msg
        await response_msg.update()
    except Exception as e:
        error_msg = f"❌ 处理消息时出错: {str(e)}"
        logger.error(error_msg)
        response_msg.content = error_msg
        await response_msg.update()


@cl.on_stop
async def on_stop():
    """用户点击停止按钮时调用"""
    logger.info("用户请求停止生成")
    # 可以在这里添加中断逻辑


if __name__ == "__main__":
    # Chainlit 会自动处理运行，但为了兼容性保留这个入口
    pass

