import zmq.asyncio
import asyncio
from typing import Optional
from loguru import logger


class AsyncZMQSocket:
    def __init__(self, socket: zmq.asyncio.Socket, socket_type: str):
        self.socket = socket
        self.socket_type = socket_type
        self._closed = False
        
    async def recv_bytes(self, flags: int = 0) -> bytes:
        """异步接收消息"""
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            data = await self.socket.recv(flags)
            return data
        except zmq.Again:
            return None
        except Exception as e:
            logger.error(f"异步接收消息失败: {e}")
            return None


    async def recv_json(self) -> Optional[dict]:
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            data = await self.socket.recv_json()
            return data
        except zmq.Again:
            return None
        except Exception as e:
            logger.error(f"异步接收JSON消息失败: {e}")
            return None
    

    async def send_bytes(self, data: bytes, flags: int = 0) -> bool:
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            await self.socket.send(data, flags)
            return True
        except Exception as e:
            logger.error(f"异步发送消息失败: {e}")
            return False
    

    async def send_json(self, data: dict, flags: int = 0) -> bool:
        """异步发送JSON消息"""
        if self._closed:
            raise RuntimeError("Socket已关闭")
        
        try:
            await self.socket.send_json(data, flags)
            return True
        except Exception as e:
            logger.error(f"异步发送JSON消息失败: {e}")
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
    
    def __init__(self, address: str, subscribe: bytes = b"", recv_timeout_ms: int = 1000, wait_ipc: bool = False):
        self.address = address
        self.subscribe = subscribe
        self.recv_timeout_ms = recv_timeout_ms
        self.wait_ipc = wait_ipc
        self.socket = None
        self.context = None
        self._closed = False
        
    async def start(self):
        try:
            self.context = zmq.asyncio.Context()
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
            
            
        except Exception as e:
            logger.error(f"启动原生异步订阅者失败: {e}")
            raise
    
    async def recv_bytes(self) -> Optional[bytes]:
        if self._closed or not self.socket:
            return None
        
        return await self.socket.recv_bytes()

    async def recv_json(self) -> Optional[dict]:
        if self._closed or not self.socket:
            return None
        
        return await self.socket.recv_json()


    async def stop(self):
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("原生异步订阅者已停止")


class AsyncZMQPublisher:
    
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
            self.context = zmq.asyncio.Context()
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
            
            
        except Exception as e:
            logger.error(f"启动原生异步发布者失败: {e}")
            raise
    
    async def send_bytes(self, data: bytes) -> bool:
        if self._closed or not self.socket:
            return False
        
        return await self.socket.send_bytes(data)
    
    async def send_json(self, data: dict) -> bool:
        if self._closed or not self.socket:
            return False
        
        return await self.socket.send_json(data)
    
    async def stop(self):
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("原生异步发布者已停止")


# 便捷函数
async def create_async_sub_native(address: str, subscribe: bytes = b"", recv_timeout_ms: int = 1000, wait_ipc: bool = False) -> AsyncZMQSubscriber:
    """创建原生异步订阅者"""
    subscriber = AsyncZMQSubscriber(address, subscribe, recv_timeout_ms, wait_ipc)
    await subscriber.start()
    return subscriber


async def create_async_pub_native(address: str, bind: bool = True, cleanup_ipc: bool = True) -> AsyncZMQPublisher:
    """创建原生异步发布者"""
    publisher = AsyncZMQPublisher(address, bind, cleanup_ipc)
    await publisher.start()
    return publisher


class AsyncZMQReplier:
    """异步ZeroMQ回复者（REP模式）"""
    
    def __init__(self, address: str, bind: bool = True, cleanup_ipc: bool = True):
        self.address = address
        self.bind = bind
        self.cleanup_ipc = cleanup_ipc
        self.socket = None
        self.context = None
        self._closed = False
        
    async def start(self):
        """启动回复者"""
        try:
            self.context = zmq.asyncio.Context()
            self.socket = AsyncZMQSocket(
                self.context.socket(zmq.REP), 
                "REP"
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
            
            logger.info(f"异步回复者已启动: {self.address}")
            
        except Exception as e:
            logger.error(f"启动异步回复者失败: {e}")
            raise
    
    async def recv_request(self) -> Optional[bytes]:
        """接收请求（REP socket必须严格遵循 recv -> send 的顺序）"""
        if self._closed or not self.socket:
            return None
        return await self.socket.recv_bytes()
    
    async def recv_request_json(self) -> Optional[dict]:
        """接收JSON请求"""
        if self._closed or not self.socket:
            return None
        return await self.socket.recv_json()
    
    async def send_reply(self, data: bytes) -> bool:
        """发送回复（REP socket必须严格遵循 recv -> send 的顺序）"""
        if self._closed or not self.socket:
            return False
        return await self.socket.send_bytes(data)
    
    async def send_reply_json(self, data: dict) -> bool:
        """发送JSON回复"""
        if self._closed or not self.socket:
            return False
        return await self.socket.send_json(data)
    
    async def stop(self):
        """停止回复者"""
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("异步回复者已停止")


class AsyncZMQRequester:
    """异步ZeroMQ请求者（REQ模式）"""
    
    def __init__(self, address: str, connect: bool = True, wait_ipc: bool = False):
        self.address = address
        self.connect = connect
        self.wait_ipc = wait_ipc
        self.socket = None
        self.context = None
        self._closed = False
        
    async def start(self):
        """启动请求者"""
        try:
            self.context = zmq.asyncio.Context()
            self.socket = AsyncZMQSocket(
                self.context.socket(zmq.REQ), 
                "REQ"
            )
            
            if self.wait_ipc and self.address.startswith('ipc://'):
                import os
                ipc_path = self.address.replace('ipc://', '')
                while not os.path.exists(ipc_path):
                    await asyncio.sleep(0.1)
            
            if self.connect:
                self.socket.socket.connect(self.address)
            else:
                self.socket.socket.bind(self.address)
            
            # 等待连接建立
            await asyncio.sleep(0.1)
            
            logger.info(f"异步请求者已启动: {self.address}")
            
        except Exception as e:
            logger.error(f"启动异步请求者失败: {e}")
            raise
    
    async def request(self, data: bytes) -> Optional[bytes]:
        """发送请求并等待回复（REQ socket必须严格遵循 send -> recv 的顺序）"""
        if self._closed or not self.socket:
            return None
        
        # REQ socket必须严格遵循 send -> recv 的顺序
        await self.socket.send_bytes(data)
        return await self.socket.recv_bytes()
    
    async def request_json(self, data: dict) -> Optional[dict]:
        """发送JSON请求并等待JSON回复"""
        if self._closed or not self.socket:
            return None
        
        await self.socket.send_json(data)
        return await self.socket.recv_json()
    
    async def stop(self):
        """停止请求者"""
        self._closed = True
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("异步请求者已停止")


# 便捷函数
async def create_async_rep_native(address: str, bind: bool = True, cleanup_ipc: bool = True) -> AsyncZMQReplier:
    """创建原生异步回复者"""
    replier = AsyncZMQReplier(address, bind, cleanup_ipc)
    await replier.start()
    return replier


async def create_async_req_native(address: str, connect: bool = True, wait_ipc: bool = False) -> AsyncZMQRequester:
    """创建原生异步请求者"""
    requester = AsyncZMQRequester(address, connect, wait_ipc)
    await requester.start()
    return requester
