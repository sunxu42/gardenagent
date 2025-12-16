from typing import Dict
from loguru import logger
from src.transport_layer.base import TransportBase
# from src.handler_layer.handler import Handler
from src.handler_layer.text_in_text_out_handler import Handler # 只支持文本输入的handler
from src.handler_layer.handler_factory import load_class

class HandlerManager:
    
    def __init__(self, transport: TransportBase, handler_type: str):
        self.transport = transport
        self.handlers = {}  # client_id -> Handler
        self.handler_type = handler_type
    
    async def create_handler(self, client_id: str):
        if client_id in self.handlers:
            logger.warning(f"客户端 {client_id} 的 Handler 已存在")
            return
        logger.debug(f"正在创建 {self.handler_type} Handler")
        handler_class = load_class(self.handler_type)
        handler = handler_class(self.transport, client_id)
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