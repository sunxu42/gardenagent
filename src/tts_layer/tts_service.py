"""
TTS 服务模块

输入（来自队列）:
- JSON，对象至少包含字段:
  - text: 字符串
    - "SENTENCE_START": 开启新的 TTS 会话
    - "SENTENCE_END": 结束当前会话
    - 其他内容: 作为 TTS 文本发送

输出（通过回调函数）:
- JSON，对象包含:
  - audio_data: 将 PCM 原始字节流做 hex 编码后的字符串
  - metadata:
      session_id: 会话 ID
      timestamp: 发送时间戳 (Unix 秒)
      end_of_stream: 是否为当前文本的最后一段音频

音频字节流规格:
- PCM16 (16-bit signed integer, little-endian)
- 采样率: 16000 Hz
- 单声道 (Mono)
- 每帧 2 字节

使用队列机制接收 Agent 文本，通过回调函数返回 TTS 音频数据
"""
import asyncio
import uuid
from typing import Callable, Dict, Any
from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.TTS)
from src.config import TTSConfig
from src.tts_layer.backends.factory import TTSFactory

def clean_markdown(text: str) -> str:
    # 移除常见的markdown标记
    import re
    # 移除粗体、斜体、代码块等
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 粗体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # 斜体
    text = re.sub(r'`([^`]+)`', r'\1', text)  # 行内代码
    text = re.sub(r'```[\s\S]*?```', '', text)  # 代码块
    text = re.sub(r'#+\s*', '', text)  # 标题
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 链接
    return text.strip()


class TTSService:

    def __init__(self, config):
        self.config = config
        self.tts_backend = TTSFactory.create(
            provider_name=config.tts_provider_name,
            config=config
        )

        self.is_running = False
        self.queue = asyncio.Queue(maxsize=1000)
        self.result_callback = None
        self.text_receiver_task = None
        self.current_session_id = None  # 当前TTS会话ID

    def set_result_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置 TTS 音频结果回调函数"""
        self.result_callback = callback

    async def start(self):
        try:
            self.is_running = True
            self.tts_backend.set_audio_callback(self._handle_audio_data)
            self.text_receiver_task = asyncio.create_task(self.text_receiver_loop())

            _log.info(
                f"TTS服务已启动,"
                f"TTS提供商: {self.config.tts_provider_name}"
            )

        except Exception as e:
            _log.error(f"启动TTS服务失败: {e}")
            await self.stop()
            raise

    async def stop(self):
        _log.info("正在停止TTS服务...")
        self.is_running = False

        if self.text_receiver_task:
            self.text_receiver_task.cancel()
            try:
                await self.text_receiver_task
            except asyncio.CancelledError:
                pass

        if self.tts_backend:
            try:
                await self.tts_backend.cleanup()
            except Exception:
                pass

        _log.info("TTS服务已停止")


    async def text_receiver_loop(self):
        while self.is_running:
            try:
                message = await self.queue.get()
                if message is not None:
                    await self.process_text_message(message)
            except asyncio.CancelledError:
                _log.info("TTS 文本接收循环已取消")
                break
            except Exception as e:
                _log.error(f"文本接收循环出错: {e}")


    async def end_session(self):
        """立即结束当前TTS会话（用于打断）"""
        try:
            if hasattr(self, 'current_session_id') and self.current_session_id:
                # 如果TTS backend支持cancel_session，优先使用（更快速）
                if hasattr(self.tts_backend, 'cancel_session'):
                    await self.tts_backend.cancel_session(self.current_session_id)
                else:
                    await self.tts_backend.finish_session(self.current_session_id)
                self.current_session_id = None
        except Exception as e:
            _log.error(f"结束TTS会话失败: {e}")

    async def process_text_message(self, message):
        try:
            text = message.get('text', '')
            if clean_markdown(text):
                # _log.debug(f"收到文本消息: {text}")
                if  text == "SENTENCE_START":
                    voice = message.get('voice_type')
                    emotion = message.get('emotion')
                    scale = message.get('emotion_scale', 4)
                    if voice and hasattr(self.tts_backend, 'set_voice'):
                        self.tts_backend.set_voice(voice)
                    if hasattr(self.tts_backend, 'set_emotion'):
                        self.tts_backend.set_emotion(emotion, scale)
                    speech_rate = message.get('speech_rate', 0)
                    pitch = message.get('pitch', 0)
                    loudness_rate = message.get('loudness_rate', 0)
                    if hasattr(self.tts_backend, 'set_prosody'):
                        self.tts_backend.set_prosody(speech_rate, pitch, loudness_rate)

                    while True:
                        self.current_session_id = str(uuid.uuid4().hex)
                        success = await self.tts_backend.start_session(self.current_session_id)

                        if success:
                            break

                elif text == "SENTENCE_END":
                    await self.tts_backend.finish_session(self.current_session_id)
                else:
                    await self.tts_backend.send_text(text)

        except Exception as e:
            _log.error(f"处理流式TTS失败: {e}")


    async def _handle_audio_data(self, audio_data, end_of_stream):

        message = {
            'audio_data': audio_data,
            'end_of_stream': end_of_stream
            }
        await self.result_callback(message)



async def main():
    tts_service = TTSService(config=TTSConfig())
    try:
        await tts_service.start()
        # 等待后台任务运行
        await tts_service.text_receiver_task
    except KeyboardInterrupt:
        _log.info("收到停止信号")
    except Exception as e:
        _log.error(f"TTS服务运行出错: {e}")
    finally:
        await tts_service.stop()


if __name__ == "__main__":
    asyncio.run(main())
