"""
音频服务模块

音频统一格式要求：
- 格式: PCM16 (16位有符号整数)
- 采样率: 16000Hz
- 声道: 单声道 (mono)
- 字节序: 小端序 (little-endian)

音频数据以字节流形式传输，每个样本占2字节（16位）。
例如：60ms的音频数据 = 16000 * 0.06 * 2 = 1920 字节

使用队列机制接收音频数据，通过回调函数返回 ASR 结果
"""
import asyncio
import signal
from typing import Callable, Dict, Any
from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.ASR)
from src.config import AudioConfig
from src.audio_layer.provider.factory import ASRFactory


class AudioService:
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.asr_service = ASRFactory.create(config.asr_provider_name, config)
        
        self.is_running = False
        self.audio_queue = asyncio.Queue(maxsize=1000)
        self.audio_processor_task = None
        self.result_callback = None

    async def start(self):

        self.asr_service.set_result_callback(self._handle_asr_result)
        try:
            self.is_running = True

            # 启动音频处理任务
            self.audio_processor_task = asyncio.create_task(self.audio_processor_loop())
            
            _log.info(
                f"音频服务已启动,"
                f"ASR提供商: {self.config.asr_provider_name}"
            )
        except Exception as e:
            _log.error(f"启动服务失败: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        _log.info("正在停止音频处理服务...")
        self.is_running = False
        
        # 取消任务
        if self.audio_processor_task:
            self.audio_processor_task.cancel()
            try:
                await self.audio_processor_task
            except asyncio.CancelledError:
                pass
        
        _log.info("音频处理服务已停止")
    
    async def audio_processor_loop(self):
        
        while self.is_running:
            try:
                audio_data = await self.audio_queue.get()
            except Exception as e:
                _log.error(f"获取音频数据出错: {e}")
                break
            if audio_data:
                try:
                    await self.asr_service.send_audio_data(audio_data)
                except Exception as e:
                    _log.error(f"发送音频数据出错: {e}")
                    

    async def _handle_asr_result(self, result: Dict[str, Any]):
        try:
            await self.result_callback(result)

        except Exception as e:
            _log.error(f"调用 ASR 结果回调失败: {e}")

    def set_result_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.result_callback = callback


async def main():
    service = AudioService(config=AudioConfig())
    
    # 设置信号处理
    def signal_handler(signum, frame):
        _log.info(f"接收到信号 {signum}，正在关闭服务...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
        # 等待后台任务运行
        await service.audio_processor_task
    except KeyboardInterrupt:
        _log.info("接收到中断信号")
    except Exception as e:
        _log.error(f"服务运行出错: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
