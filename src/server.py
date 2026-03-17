import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.transport_layer import WebSocketTransport
from src.handler_layer.handler_manager import HandlerManager
from src.log import setup_logger, logger
from src.config import WebSocketConfig
setup_logger(log_level='DEBUG',disable_modules=[])





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
        
        # 启动 HandlerManager
        await self.handler_manager.start()
        
        # 启动传输层
        await self.transport.start()
    
    async def stop(self):
        # 停止 HandlerManager
        await self.handler_manager.stop()
        # 停止传输层
        await self.transport.stop()
    
    async def _on_client_connect(self, client_id: str, is_reconnect: bool):
        await self.handler_manager.create_or_reuse_handler(client_id, is_reconnect)
    
    async def _on_client_disconnect(self, client_id: str):
        await self.handler_manager.remove_handler(client_id)
    
    async def _on_message(self, client_id: str, message):
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
