import asyncio
from src.transport_layer import WebSocketTransport
from src.handler_layer.handler_manager import HandlerManager
from src.log import setup_logger

from loguru import logger
from src.config import WebSocketConfig
setup_logger(log_level='DEBUG',disable_modules=['src.agent_layer',"fairland_brain"])





class Server:
    
    def __init__(self):
        self.transport = WebSocketTransport(host=WebSocketConfig.host, port=WebSocketConfig.port)
        self.handler_manager = HandlerManager(self.transport, WebSocketConfig.handler_type)
    
    async def start(self):
        # 注册连接和断开回调
        self.transport.register_connection_handler(
            on_connect=self._on_client_connect,
            on_disconnect=self._on_client_disconnect
        )
        
        # 注册消息处理回调
        self.transport.register_message_handler(self._on_message)
        
        # 启动传输层
        await self.transport.start()
    
    async def stop(self):
        # 清理所有 Handler
        await self.handler_manager.cleanup_all()
        # 停止传输层
        await self.transport.stop()
    
    async def _on_client_connect(self, client_id: str):
        """客户端连接时的回调"""
        await self.handler_manager.create_handler(client_id)
    
    async def _on_client_disconnect(self, client_id: str):
        """客户端断开时的回调"""
        await self.handler_manager.remove_handler(client_id)
    
    async def _on_message(self, client_id: str, message):
        """消息处理回调"""
        await self.handler_manager.handle_message(client_id, message)


async def main():
    server = Server()
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
