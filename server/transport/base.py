"""
传输层抽象基类

定义传输层的统一接口，支持不同的传输协议实现（WebSocket、HTTP/2、gRPC 等）。
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Any


class TransportBase(ABC):
    """
    传输层抽象基类
    
    定义所有传输层实现必须遵循的接口，使业务层可以独立于具体的传输协议。
    """
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        服务器是否正在运行
        
        Returns:
            是否运行中
        """
        pass
    
    @property
    @abstractmethod
    def connections(self) -> dict:
        """
        当前连接的客户端字典
        
        Returns:
            client_id -> connection 的映射
        """
        pass
    
    @abstractmethod
    def register_message_handler(self, callback: Callable[[str, Any], None]):
        """
        注册消息处理回调
        
        Args:
            callback: 回调函数，接收 (client_id, message) 参数
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def start(self):
        """
        启动传输服务器
        
        应该是一个阻塞调用，直到服务器停止。
        """
        pass
    
    @abstractmethod
    async def stop(self):
        """
        停止传输服务器
        
        应该清理所有资源，关闭所有连接。
        """
        pass
    
    @abstractmethod
    async def send_to_client(self, client_id: str, data: Any) -> bool:
        """
        发送消息到指定客户端
        
        Args:
            client_id: 客户端 ID
            data: 要发送的数据（bytes 或 str，具体格式由实现决定）
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def broadcast(self, data: Any) -> int:
        """
        广播消息到所有连接的客户端
        
        Args:
            data: 要发送的数据（bytes 或 str）
            
        Returns:
            成功发送的客户端数量
        """
        pass
    
    @abstractmethod
    def get_client_count(self) -> int:
        """
        获取当前连接的客户端数量
        
        Returns:
            客户端数量
        """
        pass
    
    @abstractmethod
    def is_client_connected(self, client_id: str) -> bool:
        """
        检查客户端是否已连接
        
        Args:
            client_id: 客户端 ID
            
        Returns:
            是否已连接
        """
        pass

