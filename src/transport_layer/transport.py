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
from typing import Dict, Set, Optional, Callable, Any
from urllib.parse import parse_qs, urlparse
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
        # 回调签名：client_id, is_reconnect
        self._on_connect_callback: Optional[Callable[[str, bool], None]] = None
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
    
    def _extract_client_id(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        """
        从 WebSocket 请求头中提取 client-id
        
        Args:
            websocket: WebSocket 连接对象
            
        Returns:
            客户端 ID，如果不存在则返回 None
        """
        try:
            # websockets 库中，通过 request_headers 访问 HTTP 请求头
            headers = websocket.request.headers
            # 尝试不同的 header 名称（大小写不敏感）
            client_id = headers.get('client-id') or headers.get('Client-Id') or headers.get('CLIENT-ID')
            if client_id:
                return client_id

            request_path = getattr(websocket.request, "path", "") or ""
            if request_path:
                query_string = urlparse(request_path).query
                if query_string:
                    params = parse_qs(query_string)
                    client_id = (params.get("client-id") or params.get("client_id") or [None])[0]
                    if client_id:
                        return client_id

            # 如果没有找到，返回 None（业务层可以拒绝连接）
            return None
        except Exception as e:
            logger.error(f"提取客户端 ID 失败: {e}")
            return None
    
    async def start(self):
        self._is_running = True
        
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            # ping_interval=self.ping_interval,
            # ping_timeout=self.ping_timeout
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
        # 从请求头提取 client_id
        client_id = self._extract_client_id(websocket)
        
        if not client_id:
            logger.error("客户端未提供 client-id，拒绝连接")
            try:
                await websocket.close(code=1008, reason="Missing client-id header")
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")
            return
        
        # 检查是否是重连（相同 client_id 的连接已存在）
        is_reconnect = client_id in self._connections
        
        if is_reconnect:
            # 立即关闭旧连接（不等待关闭完成）
            old_websocket = self._connections[client_id]
            logger.info(f"检测到客户端 {client_id} 重连，立即关闭旧连接")
            # 立即从连接池移除，避免新消息发送到旧连接
            self._connections.pop(client_id, None)
            # 后台关闭旧连接，不阻塞新连接
            asyncio.create_task(self._close_connection_async(old_websocket, client_id))
        
        logger.debug(f"客户端连接: client_id={client_id}, is_reconnect={is_reconnect}, 路径: {path}")
        
        # 先添加到连接池，确保后续操作（如 rebind_connection 发送消息）可以访问连接
        self._connections[client_id] = websocket
        
        # 调用连接回调
        if self._on_connect_callback:
            try:
                await self._on_connect_callback(client_id, is_reconnect)
            except Exception as e:
                logger.error(f"连接建立回调失败: {e}, 关闭连接")
                # 如果回调失败，从连接池移除
                self._connections.pop(client_id, None)
                try:
                    await websocket.close(code=1011, reason="Handler initialization failed")
                except Exception as close_error:
                    logger.error(f"关闭连接失败: {close_error}")
                return
        
        logger.info(f"客户端连接已建立: client_id={client_id}, is_reconnect={is_reconnect}")
        
        try:
            # 消息循环
            async for message in websocket:
                await self._on_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: client_id={client_id}")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 消息失败: {e}")
        finally:
            # 清理连接
            if self._connections.get(client_id) == websocket:
                self._connections.pop(client_id, None)
            
            if self._connections.get(client_id) != websocket:
                # 这是被替换的旧连接，不触发断开回调
                logger.debug(f"旧连接 {client_id} 被替换，不触发断开回调")
            elif self._on_disconnect_callback:
                try:
                    await self._on_disconnect_callback(client_id)
                except Exception as e:
                    logger.error(f"连接断开回调失败: {e}")
    
    async def _close_connection_async(self, websocket: WebSocketServerProtocol, client_id: str):
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

