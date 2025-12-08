#!/usr/bin/env python3
import asyncio
import numpy as np
import time
import json
from loguru import logger
from src.config import AudioConfig as Config
from src.utils.async_zmq_utils_native import create_async_pub_native, create_async_sub_native


class StreamingAudioTest:
    def __init__(self):
        self.audio_publisher = None
        self.text_subscriber = None
        self.is_running = False
        self.audio_data = None
        self.sample_rate = 16000
        self.chunk_duration = 0.06  # 60ms
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
    async def start(self):
        try:
            # 创建音频发布者
            self.audio_publisher = await create_async_pub_native(Config.ASR_LISTEN_ADDRESS, bind=True, cleanup_ipc=True)
            
            # 创建文本订阅者
            self.text_subscriber = await create_async_sub_native(Config.ASR_PUBLISH_ADDRESS, subscribe=b"", recv_timeout_ms=1000, wait_ipc=True)
            
            self.is_running = True
            logger.info("流式音频测试客户端已启动")
            
        except Exception as e:
            logger.error(f"启动测试客户端失败: {e}")
            raise
    
    async def stop(self):
        self.is_running = False
        if self.audio_publisher:
            await self.audio_publisher.stop()
        if self.text_subscriber:
            await self.text_subscriber.stop()
        logger.info("测试客户端已停止")
    
    def load_audio_file(self, file_path: str):
        try:
            import librosa
            import numpy as np
            
            # 使用librosa加载音频，自动重采样到16kHz
            audio_data, original_sr = librosa.load(file_path, sr=16000, mono=True)
            
            logger.info(f"加载音频文件: {file_path}")
            logger.info(f"原始采样率: {original_sr}Hz -> 重采样到: 16000Hz")
            logger.info(f"音频长度: {len(audio_data)} 样本")
            
            # 转换为16位PCM格式
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # 转换为字节数据
            self.audio_data = audio_int16.tobytes()
            logger.info(f"PCM数据长度: {len(self.audio_data)} bytes (16位单声道)")
            
            return True
                
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            return False
    

    async def send_audio_stream(self, audio_pcm_bytes):
        logger.info(f"开始发送PCM音频流，总长度: {len(audio_pcm_bytes)} bytes")
        logger.info(f"块大小: {self.chunk_size * 2} bytes，块间隔: {self.chunk_duration * 1000}ms")
        
        chunk_bytes_size = self.chunk_size * 2  # 16位 = 2字节
        total_chunks = len(audio_pcm_bytes) // chunk_bytes_size
        logger.info(f"将发送 {total_chunks} 个PCM音频块")
        t = time.time()
        for i in range(0, len(audio_pcm_bytes), chunk_bytes_size):
            chunk_bytes = audio_pcm_bytes[i:i + chunk_bytes_size]
            
            # 如果块不够大，用零填充
            if len(chunk_bytes) < chunk_bytes_size:
                padding = b'\x00' * (chunk_bytes_size - len(chunk_bytes))
                chunk_bytes = chunk_bytes + padding
            
            # 发送PCM数据
            await self.audio_publisher.send_bytes(chunk_bytes)
            
            logger.debug(f"发送PCM块 {i // chunk_bytes_size + 1}/{total_chunks}, 大小: {len(chunk_bytes)} bytes")
            
            # 严格按照60ms间隔发送
            await asyncio.sleep(self.chunk_duration)
            self.last_chunk_send_time = time.time()
        logger.info(f"PCM音频流发送完成，耗时: {time.time() - t}秒")
        logger.info("PCM音频流发送完成")
    
    async def receive_text_results(self, duration: int = 60):
        logger.info(f"开始接收文本结果，持续时间: {duration}秒")
        
        start_time = time.time()
        message_count = 0
        
        while (time.time() - start_time) < duration and self.is_running:
            try:
                data = await self.text_subscriber.recv_json()
                if data:
                    latency = time.time() - self.last_chunk_send_time
                    message_count += 1
                    logger.info(f"延迟: {latency}秒, 收到识别结果 {message_count}: {data['text']}, {data['is_final']}")
                else:
                    await asyncio.sleep(0.1)
                    continue
            except Exception as e:
                logger.error(f"接收文本结果失败: {e}")
                await asyncio.sleep(0.1)
        
        logger.info(f"文本结果接收完成，共收到 {message_count} 条消息")
    
    async def run_test(self, audio_file: str = None):
        if audio_file and os.path.exists(audio_file):
            logger.info(f"使用音频文件: {audio_file}")
            if not self.load_audio_file(audio_file):
                logger.warning("加载音频文件失败")
                return
            else:
                audio_pcm_bytes = self.audio_data
        else:
            logger.warning("未提供音频文件")
            return
        
        try:
            logger.info("开始PCM流式测试")
            audio_task = asyncio.create_task(self.send_audio_stream(audio_pcm_bytes))
            text_task = asyncio.create_task(self.receive_text_results(60))
            
            await asyncio.gather(audio_task, text_task)
            
        except Exception as e:
            logger.error(f"PCM流式测试失败: {e}")
        finally:
            await self.stop()


async def main():
    import sys
    
    audio_file = "audio_layer/test.wav"
    
    client = StreamingAudioTest()
    
    try:
        await client.start()
        await client.run_test(audio_file)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
