#!/usr/bin/env python3
"""
Utility script to smoke-test `src/audio_layer/audio_service.py`.

It publishes audio data to the ASR listen address
(`ASR_LISTEN_ADDRESS`) and listens for text results from
`ASR_PUBLISH_ADDRESS`. Once text is received, it prints the results.

Requirements:
    pip install librosa numpy  # for loading audio files
    Provide an audio file (will be converted to PCM16, 16000Hz, mono)
    Default file: test.wav in the same directory
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import Optional, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import AudioConfig
from src.utils.async_zmq_utils_native import (
    create_async_pub_native,
    create_async_sub_native,
)

try:
    import librosa
    import numpy as np
except ImportError:
    librosa = None
    np = None


class ASRSmokeTester:
    """Publishes test audio and captures the returning text results."""

    def __init__(
        self,
        audio_data: Optional[bytes] = None,
        audio_file: Optional[Path] = None,
        timeout: float = 30.0,
    ):
        self.audio_data = audio_data
        self.audio_file = audio_file
        self.timeout = timeout

        self.config = AudioConfig()
        self.audio_publisher = None
        self.text_subscriber = None

        self.results: List[dict] = []
        self.final_text: Optional[str] = None

    async def __aenter__(self):
        await self._setup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._teardown()

    async def _setup(self):
        """Initialise PUB/SUB sockets."""
        self.audio_publisher = await create_async_pub_native(
            self.config.asr_listen_address,
            bind=True,
            cleanup_ipc=False,
        )
        # Give subscribers a moment to connect
        await asyncio.sleep(0.2)

        self.text_subscriber = await create_async_sub_native(
            self.config.asr_publish_address,
            subscribe=b"",
            recv_timeout_ms=1000,
            wait_ipc=True,
        )

    async def _teardown(self):
        if self.audio_publisher:
            await self.audio_publisher.stop()
        if self.text_subscriber:
            await self.text_subscriber.stop()

    def _load_audio_data(self) -> bytes:
        """Load audio data from file and convert to PCM16 format."""
        if self.audio_data:
            return self.audio_data

        if not self.audio_file or not self.audio_file.exists():
            raise RuntimeError(
                f"音频文件不存在: {self.audio_file}\n"
                "请提供有效的音频文件"
            )
        
        if librosa is None or np is None:
            raise RuntimeError(
                "需要安装 librosa 和 numpy 来处理音频文件。\n"
                "运行: pip install librosa numpy"
            )
        
        try:
            # 使用librosa加载音频，自动重采样到16kHz
            audio_data, original_sr = librosa.load(str(self.audio_file), sr=16000, mono=True)
            
            print(f"加载音频文件: {self.audio_file}")
            print(f"原始采样率: {original_sr}Hz -> 重采样到: 16000Hz")
            print(f"音频长度: {len(audio_data)} 样本")
            
            # 转换为16位PCM格式
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # 转换为字节数据
            pcm_bytes = audio_int16.tobytes()
            print(f"PCM数据长度: {len(pcm_bytes)} bytes (16位单声道)")
            
            return pcm_bytes
                
        except Exception as e:
            raise RuntimeError(f"加载音频文件失败: {e}")

    async def send_test_audio(self, chunk_size: int = 1920):
        """Send audio data in chunks to simulate streaming."""
        audio_data = self._load_audio_data()
        total_bytes = len(audio_data)
        sent_bytes = 0

        print(f"开始发送音频数据 ({total_bytes} 字节)...")

        while sent_bytes < total_bytes:
            chunk = audio_data[sent_bytes : sent_bytes + chunk_size]
            if not chunk:
                break

            await self.audio_publisher.send_bytes(chunk)
            sent_bytes += len(chunk)

            # Delay to simulate real-time streaming (60ms per chunk)
            await asyncio.sleep(0.06)  # 60ms per chunk

        print(f"✅ 音频数据发送完成 ({sent_bytes} 字节)")

    async def collect_text_results(self) -> List[dict]:
        """Listen for text results until final flag or timeout."""
        deadline = time.monotonic() + self.timeout
        self.results = []

        print(f"开始监听文本结果 (超时: {self.timeout}秒)...")

        while time.monotonic() < deadline:
            try:
                message = await self.text_subscriber.recv_json()
                if not message:
                    await asyncio.sleep(0.05)
                    continue

                text = message.get("text", "")
                is_final = message.get("is_final", False)

                if text:
                    result = {"text": text, "is_final": is_final, "raw": message}
                    self.results.append(result)
                    print(f"📝 收到文本: {text} {'(最终结果)' if is_final else '(中间结果)'}")

                if is_final:
                    self.final_text = text
                    print("✅ 收到最终结果，停止监听")
                    break

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚠️  接收消息时出错: {e}")
                await asyncio.sleep(0.1)

        if not self.results:
            raise RuntimeError("未在超时时间内收到任何文本结果")

        return self.results


async def main(args):
    audio_data = None
    
    # 确定音频文件路径
    if args.audio_file:
        audio_file = Path(args.audio_file).expanduser().resolve()
    else:
        # 使用默认文件 test.wav（与脚本同目录）
        script_dir = Path(__file__).parent
        audio_file = script_dir / "test.wav"
    
    if not audio_file.exists():
        print(f"❌ 音频文件不存在: {audio_file}")
        print(f"   请确保文件存在，或使用 --audio-file 指定其他文件")
        return

    async with ASRSmokeTester(
        audio_data=audio_data,
        audio_file=audio_file,
        timeout=args.timeout,
    ) as tester:
        # Start listening for results in background
        listen_task = asyncio.create_task(tester.collect_text_results())

        # Send audio data
        await tester.send_test_audio(chunk_size=args.chunk_size)

        # Wait for results
        try:
            await asyncio.wait_for(listen_task, timeout=args.timeout + 5)
        except asyncio.TimeoutError:
            print("⚠️  等待结果超时")

        # Print summary
        print("\n" + "=" * 50)
        print("测试结果摘要:")
        print(f"  收到结果数量: {len(tester.results)}")
        if tester.final_text:
            print(f"  最终识别文本: {tester.final_text}")
        else:
            print("  ⚠️  未收到最终结果")
        print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="向 ASR 服务发送测试音频并接收识别文本结果"
    )
    parser.add_argument(
        "--audio-file",
        type=str,
        help="要发送的音频文件路径（将自动转换为PCM16格式，16000Hz，单声道）。默认使用 test.wav",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1920,
        help="每次发送的音频块大小（字节），默认1920（60ms@16kHz PCM16）",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="等待文本返回的超时时间（秒）",
    )

    asyncio.run(main(parser.parse_args()))

