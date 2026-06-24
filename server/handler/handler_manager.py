import asyncio
from typing import Dict, Optional, Any
from shared.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.HANDLER)
from shared.config.server import UnifiedConfig
from server.transport.base import TransportBase
from server.handler.handler_factory import load_class


class HandlerManager:

    def __init__(
        self,
        transport: TransportBase,
        handler_type: str,
        server_config: UnifiedConfig,
        reconnect_timeout: int = 300,
    ):
        self.transport = transport
        self.handlers: Dict[str, Any] = {}
        self.handler_type = handler_type
        self.server_config = server_config
        self.reconnect_timeout = reconnect_timeout  # 重连超时时间（秒）
        
        # 启动清理任务
        self._cleanup_task = None
    
    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_disconnected_handlers())
    
    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.cleanup_all()
    
    async def _cleanup_disconnected_handlers(self):
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                current_time = asyncio.get_event_loop().time()
                
                disconnected_handlers = []
                for client_id, handler in self.handlers.items():
                    # 检查 Handler 是否已断开且超过超时时间
                    if hasattr(handler, '_disconnected_at'):
                        if handler._disconnected_at and (current_time - handler._disconnected_at) > self.reconnect_timeout:
                            disconnected_handlers.append(client_id)
                
                for client_id in disconnected_handlers:
                    _log.info(f"清理超时未重连的 Handler: client_id={client_id}")
                    await self._remove_handler_internal(client_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                _log.error(f"清理断开连接 Handler 时出错: {e}")
    
    async def create_or_reuse_handler(self, client_id: str, is_reconnect: bool):
        # 页面刷新时旧 WebSocket 已从连接池移除，is_reconnect 常为 False，但 Handler 仍在
        # reconnect_timeout 窗口内 — 必须复用以保留 MemorySaver 多轮 checkpoint。
        if client_id in self.handlers:
            handler = self.handlers[client_id]
            _log.info(
                f"复用 Handler: client_id={client_id}, transport_reconnect={is_reconnect}"
            )
            if hasattr(handler, "rebind_connection"):
                await handler.rebind_connection()
            if hasattr(handler, "_disconnected_at"):
                handler._disconnected_at = None
            return

        _log.debug(f"正在创建 {self.handler_type} Handler: client_id={client_id}")
        handler = load_class(
            self.handler_type, self.transport, client_id, self.server_config
        )
        self.handlers[client_id] = handler
        await handler.setup_services()
    
    async def remove_handler(self, client_id: str):
        """
        标记 Handler 为断开状态（不立即删除，等待重连）
        
        Args:
            client_id: 客户端 ID
        """
        if client_id in self.handlers:
            handler = self.handlers[client_id]
            # 标记为断开，但不删除
            handler._disconnected_at = asyncio.get_event_loop().time()
            _log.info(f"Handler 已断开，等待重连: client_id={client_id}, timeout={self.reconnect_timeout}s")
        else:
            _log.warning(f"客户端 {client_id} 的 Handler 不存在")
    
    async def _remove_handler_internal(self, client_id: str):
        """内部方法：真正删除 Handler"""
        if client_id not in self.handlers:
            return
        
        _log.info(f"清理客户端 {client_id} 的 Handler")
        handler = self.handlers[client_id]
        
        # 清理服务
        await handler.cleanup_services()
        
        # 移除 Handler
        del self.handlers[client_id]
    
    async def handle_message(self, client_id: str, message):
        handler = self.handlers.get(client_id)
        if handler:
            await handler.on_message(client_id, message)
        else:
            _log.warning(f"客户端 {client_id} 的 Handler 不存在，无法处理消息")
    
    async def cleanup_all(self):
        _log.info("清理所有 Handler")
        for client_id in list(self.handlers.keys()):
            await self._remove_handler_internal(client_id)