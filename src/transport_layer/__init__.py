"""
传输层模块

提供传输层抽象接口和 WebSocket 传输层实现。
支持多种传输协议，业务层与具体传输实现解耦。
"""

from .base import TransportBase
from .transport import WebSocketTransport

__all__ = ['TransportBase', 'WebSocketTransport']

