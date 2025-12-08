import zmq
import asyncio
from loguru import logger

async def create_sub(address: str, subscribe: bytes = b"", recv_timeout_ms: int = 1000, wait_ipc: bool = False):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    
    if wait_ipc and address.startswith('ipc://'):
        import os
        ipc_path = address.replace('ipc://', '')
        while not os.path.exists(ipc_path):
            await asyncio.sleep(0.1)
    
    socket.connect(address)
    socket.setsockopt(zmq.SUBSCRIBE, subscribe)
    socket.setsockopt(zmq.RCVTIMEO, recv_timeout_ms)
    
    return socket

async def create_pub(address: str, bind: bool = True):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    
    if bind:
        socket.bind(address)
    else:
        socket.connect(address)
    
    return socket
