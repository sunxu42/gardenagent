import zmq
import asyncio
import threading
from typing import Optional, Callable, Any
from loguru import logger


class AsyncZMQSocket:
    """异步ZeroMQ Socket包装器"""
    
    def __init__(self, socket: zmq.Socket, socket_type: str):
        self.socket = socket
        self.socket_type = socket_type
        self._loop = asyncio.get_event_loop()
        self._executor = None
        self._closed = False
        
    def _run_in_executor(self, func, *args):
        """在线程池中运行同步函数"""
        if self._executor is None:
            self._executor = asyncio.get_event_loop().run_in_executor
        return self._executor(None, func, *args)
    
    async def recv_async(self, flags: int = 0) -> bytes:
        """异步接收消息"""
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            # 使用线程池执行同步的recv操作
            data = await self._run_in_executor(self.socket.recv, flags)
            return data
        except zmq.Again:
            return None
        except Exception as e:
            logger.error(f"异步接收消息失败: {e}")
            return None
    
    async def send_async(self, data: bytes, flags: int = 0) -> bool:
        """异步发送消息"""
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            # 使用线程池执行同步的send操作
            await self._run_in_executor(self.socket.send, data, flags)
            return True
        except Exception as e:
            logger.error(f"异步发送消息失败: {e}")
            return False
    
    def close(self):
        """关闭socket"""
        if not self._closed:
            self._closed = True
            self.socket.close()
    
    def __del__(self):
        """析构函数"""
        if not self._closed:
            self.close()


class AsyncZMQSubscriber:
    """异步ZeroMQ订阅者"""
    
    def __init__(self, address: str, subscribe: bytes = b"", recv_timeout_ms: int = 1000, wait_ipc: bool = False):
        self.address = address
        self.subscribe = subscribe
        self.recv_timeout_ms = recv_timeout_ms
        self.wait_ipc = wait_ipc
        self.socket = None
        self.context = None
        self._closed = False
        
    async def start(self):
        """启动订阅者"""
        try:
            self.context = zmq.Context()
            self.socket = AsyncZMQSocket(
                self.context.socket(zmq.SUB), 
                "SUB"
            )
            
            if self.wait_ipc and self.address.startswith('ipc://'):
                import os
                ipc_path = self.address.replace('ipc://', '')
                while not os.path.exists(ipc_path):
                    await asyncio.sleep(0.1)
            
            self.socket.socket.connect(self.address)
            self.socket.socket.setsockopt(zmq.SUBSCRIBE, self.subscribe)
            self.socket.socket.setsockopt(zmq.RCVTIMEO, self.recv_timeout_ms)
            
            logger.info(f"异步订阅者已启动: {self.address}")
            
        except Exception as e:
            logger.error(f"启动异步订阅者失败: {e}")
            raise
    
    async def recv_message(self) -> Optional[bytes]:
        """异步接收消息"""
        if self._closed or not self.socket:
            return None
        
        return await self.socket.recv_async()
    
    async def stop(self):
        """停止订阅者"""
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("异步订阅者已停止")


class AsyncZMQPublisher:
    """异步ZeroMQ发布者"""
    
    def __init__(self, address: str, bind: bool = True, cleanup_ipc: bool = True):
        self.address = address
        self.bind = bind
        self.cleanup_ipc = cleanup_ipc
        self.socket = None
        self.context = None
        self._closed = False
        
    async def start(self):
        """启动发布者"""
        try:
            self.context = zmq.Context()
            self.socket = AsyncZMQSocket(
                self.context.socket(zmq.PUB), 
                "PUB"
            )
            
            if self.cleanup_ipc and self.address.startswith('ipc://'):
                import os
                ipc_path = self.address.replace('ipc://', '')
                if os.path.exists(ipc_path):
                    try:
                        os.unlink(ipc_path)
                    except OSError:
                        pass
            
            if self.bind:
                self.socket.socket.bind(self.address)
            else:
                self.socket.socket.connect(self.address)
            
            # 等待连接建立
            await asyncio.sleep(0.1)
            
            logger.info(f"异步发布者已启动: {self.address}")
            
        except Exception as e:
            logger.error(f"启动异步发布者失败: {e}")
            raise
    
    async def send_message(self, data: bytes) -> bool:
        """异步发送消息"""
        if self._closed or not self.socket:
            return False
        
        return await self.socket.send_async(data)
    
    async def stop(self):
        """停止发布者"""
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("异步发布者已停止")


# 便捷函数
async def create_async_sub(address: str, subscribe: bytes = b"", recv_timeout_ms: int = 1000, wait_ipc: bool = False) -> AsyncZMQSubscriber:
    """创建异步订阅者"""
    subscriber = AsyncZMQSubscriber(address, subscribe, recv_timeout_ms, wait_ipc)
    await subscriber.start()
    return subscriber


async def create_async_pub(address: str, bind: bool = True, cleanup_ipc: bool = True) -> AsyncZMQPublisher:
    """创建异步发布者"""
    publisher = AsyncZMQPublisher(address, bind, cleanup_ipc)
    await publisher.start()
    return publisher
