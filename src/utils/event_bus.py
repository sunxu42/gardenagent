import time
from typing import Any, Dict, Optional

from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

from src.utils.async_zmq_utils_native import (
    create_async_pub_native,
    create_async_sub_native,
    AsyncZMQPublisher,
    AsyncZMQSubscriber,
)
from src.config import Config


def make_event_message(event_type: str, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    构造统一的事件消息
    
    Args:
        event_type: 事件类型，如 "INTERRUPT", "SESSION_START", "SESSION_END" 等
        session_id: 会话ID，可选
        **kwargs: 其他事件参数
    """
    message = {
        "type": "control",
        "event": event_type,
        "timestamp": time.time(),
    }
    
    if session_id is not None:
        message["session_id"] = session_id
    
    # 添加其他参数
    message.update(kwargs)
    
    return message


class EventBus:
    CONTROL_ADDRESS = getattr(Config, "CONTROL_BUS_ADDRESS", "ipc:///tmp/control_bus")

    @classmethod
    async def create_publisher(cls) -> AsyncZMQPublisher:

        publisher = await create_async_pub_native(
            cls.CONTROL_ADDRESS,
            bind=True,
        )
        _log.debug(f"EventBus Publisher started at {cls.CONTROL_ADDRESS}")
        return publisher

    @classmethod
    async def create_subscriber(cls) -> AsyncZMQSubscriber:
        subscriber = await create_async_sub_native(
            cls.CONTROL_ADDRESS,
            subscribe=b"",
            recv_timeout_ms=1000,
            wait_ipc=True,
        )
        _log.debug(f"EventBus Subscriber connected to {cls.CONTROL_ADDRESS}")
        return subscriber

