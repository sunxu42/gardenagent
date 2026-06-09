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
from typing import Dict, Optional, Callable, Any
from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect
from .base import TransportBase


class WebSocketTransport(TransportBase):
    
    def __init__(self, host: str = None, port: int = None, ping_interval: int = 20, ping_timeout: int = 10):
        self.host = host 
        self.port = port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        self._connections: Dict[str, WebSocket] = {}  # client_id -> websocket
        self._is_running = False
        
        self._on_message_callback: Optional[Callable[[str, Any], None]] = None
        # 回调签名：client_id, is_reconnect
        self._on_connect_callback: Optional[Callable[[str, bool], None]] = None
        self._on_disconnect_callback: Optional[Callable[[str], None]] = None
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def connections(self) -> Dict[str, WebSocket]:
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
        on_connect: Optional[Callable[[str, bool], None]] = None,
        on_disconnect: Optional[Callable[[str], None]] = None
    ):
        """
        注册连接事件回调
        
        Args:
            on_connect: 连接建立时的回调，接收 (client_id, is_reconnect) 参数
            on_disconnect: 连接断开时的回调，接收 client_id 参数
        """
        self._on_connect_callback = on_connect
        self._on_disconnect_callback = on_disconnect
    
    def _extract_client_id(self, websocket: WebSocket) -> Optional[str]:
        """
        从 WebSocket 请求头或查询参数中提取 client-id
        
        Args:
            websocket: WebSocket 连接对象
            
        Returns:
            客户端 ID，如果不存在则返回 None
        """
        try:
            headers = websocket.headers
            client_id = (
                headers.get('client-id')
                or headers.get('Client-Id')
                or headers.get('CLIENT-ID')
            )
            if client_id:
                return client_id

            client_id = (
                websocket.query_params.get('client-id')
                or websocket.query_params.get('client_id')
            )
            if client_id:
                return client_id

            return None
        except Exception as e:
            logger.error(f"提取客户端 ID 失败: {e}")
            return None
    
    async def start(self):
        self._is_running = True
    
    async def stop(self):
        self._is_running = False
        
        for client_id, websocket in list(self._connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"关闭连接 {client_id} 失败: {e}")
        
        self._connections.clear()
        logger.info("WebSocket服务器已停止")
    
    async def handle_starlette_connection(self, websocket: WebSocket) -> None:
        await websocket.accept()

        client_id = self._extract_client_id(websocket)
        
        if not client_id:
            logger.error("客户端未提供 client-id，拒绝连接")
            try:
                await websocket.close(code=1008, reason="Missing client-id header")
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")
            return
        
        is_reconnect = client_id in self._connections
        
        if is_reconnect:
            old_websocket = self._connections[client_id]
            logger.info(f"检测到客户端 {client_id} 重连，立即关闭旧连接")
            self._connections.pop(client_id, None)
            asyncio.create_task(self._close_connection_async(old_websocket, client_id))
        
        logger.debug(f"客户端连接: client_id={client_id}, is_reconnect={is_reconnect}")
        
        self._connections[client_id] = websocket
        
        if self._on_connect_callback:
            try:
                await self._on_connect_callback(client_id, is_reconnect)
            except Exception as e:
                logger.error(f"连接建立回调失败: {e}, 关闭连接")
                self._connections.pop(client_id, None)
                try:
                    await websocket.close(code=1011, reason="Handler initialization failed")
                except Exception as close_error:
                    logger.error(f"关闭连接失败: {close_error}")
                return
        
        logger.info(f"客户端连接已建立: client_id={client_id}, is_reconnect={is_reconnect}")
        
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
                if message["type"] == "websocket.receive":
                    if "text" in message:
                        await self._on_message(client_id, message["text"])
                    elif "bytes" in message:
                        await self._on_message(client_id, message["bytes"])
                
        except WebSocketDisconnect:
            logger.info(f"客户端断开连接: client_id={client_id}")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息失败: {e}")
        finally:
            if self._connections.get(client_id) == websocket:
                self._connections.pop(client_id, None)
            
            if self._connections.get(client_id) != websocket:
                logger.debug(f"旧连接 {client_id} 被替换，不触发断开回调")
            elif self._on_disconnect_callback:
                try:
                    await self._on_disconnect_callback(client_id)
                except Exception as e:
                    logger.error(f"连接断开回调失败: {e}")
    
    async def _close_connection_async(self, websocket: WebSocket, client_id: str):
        """后台关闭连接（不阻塞主流程）"""
        try:
            await websocket.close(code=1000, reason="Reconnected")
        except Exception as e:
            logger.debug(f"后台关闭连接 {client_id} 完成: {e}")
    
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
    
    async def _send_data(self, websocket: WebSocket, data: Any) -> None:
        if isinstance(data, str):
            await websocket.send_text(data)
        elif isinstance(data, bytes):
            await websocket.send_bytes(data)
        else:
            await websocket.send_text(str(data))
    
    async def send_to_client(self, client_id: str, data: Any) -> bool:
        websocket = self._connections.get(client_id)
        if not websocket:
            logger.warning(f"客户端 {client_id} 不存在，无法发送消息")
            return False
        
        try:
            await self._send_data(websocket, data)
            return True
        except WebSocketDisconnect:
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
                await self._send_data(websocket, data)
                success_count += 1
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"广播消息到客户端 {client_id} 失败: {e}")
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self._connections.pop(client_id, None)
        
        return success_count
    
    def get_client_count(self) -> int:
        return len(self._connections)
    
    def is_client_connected(self, client_id: str) -> bool:
        return client_id in self._connections
