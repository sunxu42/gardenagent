"""
WebSocket 传输层实现

负责 WebSocket 连接的底层管理，包括：
- 连接建立、维护、关闭
- 消息的接收和发送（原始层面）
- 连接池管理
- 心跳管理
- 异常处理
"""

import asyncio
import uuid
from typing import Dict, Set, Optional, Callable, Any
from loguru import logger
import websockets
from websockets.server import WebSocketServerProtocol
from .base import TransportBase


class WebSocketTransport(TransportBase):
    
    def __init__(self, host: str = None, port: int = None, ping_interval: int = 20, ping_timeout: int = 10):
        self.host = host 
        self.port = port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        self._connections: Dict[str, WebSocketServerProtocol] = {}  # client_id -> websocket
        self._is_running = False
        self._server = None
        
        self._on_message_callback: Optional[Callable[[str, Any], None]] = None
        self._on_connect_callback: Optional[Callable[[str], None]] = None
        self._on_disconnect_callback: Optional[Callable[[str], None]] = None
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def connections(self) -> Dict[str, WebSocketServerProtocol]:
        return self._connections
    
    def register_message_handler(self, callback: Callable[[str, Any], None]):
        """
        注册消息处理回调
        
        Args:
            callback: 回调函数，接收 (client_id, message) 参数
        """
        self._on_message_callback = callback
    
    def register_connection_handler(
        self, 
        on_connect: Optional[Callable[[str], None]] = None,
        on_disconnect: Optional[Callable[[str], None]] = None
    ):
        """
        注册连接事件回调
        
        Args:
            on_connect: 连接建立时的回调，接收 client_id 参数
            on_disconnect: 连接断开时的回调，接收 client_id 参数
        """
        self._on_connect_callback = on_connect
        self._on_disconnect_callback = on_disconnect
    
    async def start(self):
        self._is_running = True
        
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout
        ) as server:
            self._server = server
            logger.info(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")
            await asyncio.Future()  # 永久运行
    
    async def stop(self):
        self._is_running = False
        
        # 关闭所有连接
        for client_id, websocket in list(self._connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"关闭连接 {client_id} 失败: {e}")
        
        self._connections.clear()
        logger.info("WebSocket服务器已停止")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str = ""):
        client_id = uuid.uuid4().hex
        logger.debug(f"客户端连接: {client_id}, 路径: {path}")
        
        if self._on_connect_callback:
            try:
                await self._on_connect_callback(client_id)
            except Exception as e:
                logger.error(f"连接建立回调失败: {e}, 关闭连接")
                # 回调失败，关闭连接并拒绝连接
                try:
                    await websocket.close(code=1011, reason="Handler initialization failed")
                except Exception as close_error:
                    logger.error(f"关闭连接失败: {close_error}")
                return  # 直接返回，不处理消息，不添加到连接池
        
        self._connections[client_id] = websocket
        logger.info(f"客户端连接已建立并添加到连接池")
        
        try:
            # 消息循环
            async for message in websocket:
                await self._on_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: {client_id}")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息失败: {e}")
        finally:
            # 清理连接
            self._connections.pop(client_id, None)
            
            # 通知业务层连接断开
            if self._on_disconnect_callback:
                try:
                    await self._on_disconnect_callback(client_id)
                except Exception as e:
                    logger.error(f"连接断开回调失败: {e}")
    
    async def _on_message(self, client_id: str, message: Any):
        """
        处理接收到的消息
        
        Args:
            client_id: 客户端 ID
            message: 消息内容（bytes 或 str）
        """
        if self._on_message_callback:
            try:
                await self._on_message_callback(client_id, message)
            except Exception as e:
                logger.error(f"消息处理回调失败 (client_id={client_id}): {e}")
        else:
            logger.warning(f"收到消息但未注册消息处理器: {client_id}")
    
    async def send_to_client(self, client_id: str, data: Any) -> bool:
        websocket = self._connections.get(client_id)
        if not websocket:
            logger.warning(f"客户端 {client_id} 不存在，无法发送消息")
            return False
        
        try:
            await websocket.send(data)
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"客户端 {client_id} 连接已关闭")
            self._connections.pop(client_id, None)
            return False
        except Exception as e:
            logger.error(f"发送消息到客户端 {client_id} 失败: {e}")
            return False
    
    async def broadcast(self, data: Any) -> int:
        success_count = 0
        disconnected_clients = []
        
        for client_id, websocket in list(self._connections.items()):
            try:
                await websocket.send(data)
                success_count += 1
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"广播消息到客户端 {client_id} 失败: {e}")
                disconnected_clients.append(client_id)
        
        # 清理已断开的连接
        for client_id in disconnected_clients:
            self._connections.pop(client_id, None)
        
        return success_count
    
    def get_client_count(self) -> int:
        return len(self._connections)
    
    def is_client_connected(self, client_id: str) -> bool:
        return client_id in self._connections

