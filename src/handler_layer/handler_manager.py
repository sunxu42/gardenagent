from typing import Dict
from loguru import logger
from src.transport_layer.base import TransportBase
from src.handler_layer.handler import Handler

class HandlerManager:
    
    def __init__(self, transport: TransportBase):
        self.transport = transport
        self.handlers: Dict[str, Handler] = {}  # client_id -> Handler
    
    async def create_handler(self, client_id: str):
        if client_id in self.handlers:
            logger.warning(f"客户端 {client_id} 的 Handler 已存在")
            return
        logger.debug(f"正在创建 Handler")
        handler = Handler(self.transport, client_id)
        self.handlers[client_id] = handler
        
        # 启动服务
        await handler.setup_services()
    
    async def remove_handler(self, client_id: str):
        if client_id not in self.handlers:
            logger.warning(f"客户端 {client_id} 的 Handler 不存在")
            return
        
        logger.info(f"清理客户端 {client_id} 的 Handler")
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
            logger.warning(f"客户端 {client_id} 的 Handler 不存在，无法处理消息")
    
    async def cleanup_all(self):
        logger.info("清理所有 Handler")
        for client_id in list(self.handlers.keys()):
            await self.remove_handler(client_id)