#!/usr/bin/env python3
"""
Utility script to smoke-test `src/tts_layer/tts_service.py`.

It publishes a short text message to the TTS text input address
(`TTS_LISTEN_ADDRESS`) and listens for audio chunks from
`TTS_PUBLISH_ADDRESS`. Once audio is received, it is converted to MP3
and saved under the provided output directory.

Requirements:
    pip install pydub
    # and ensure ffmpeg/avlib is available on PATH for MP3 export
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import TTSConfig
from src.utils.async_zmq_utils_native import (
    create_async_pub_native,
    create_async_sub_native,
)

try:
    from pydub import AudioSegment  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    AudioSegment = None


class TTSSmokeTester:
    """Publishes test text and captures the returning audio stream."""

    def __init__(self, text: str, output_dir: Path, timeout: float = 30.0):
        self.text = text
        self.timeout = timeout
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = TTSConfig()
        self.text_publisher = None
        self.audio_subscriber = None

        self.session_id: Optional[str] = None
        self.audio_buffer = bytearray()

    async def __aenter__(self):
        await self._setup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._teardown()

    async def _setup(self):
        """Initialise PUB/SUB sockets."""
        self.text_publisher = await create_async_pub_native(
            self.config.tts_listen_address,
            bind=True,  
            cleanup_ipc=False,
        )
        # Give subscribers a moment to connect
        await asyncio.sleep(0.2)

        self.audio_subscriber = await create_async_sub_native(
            self.config.tts_publish_address,
            subscribe=b"",
            recv_timeout_ms=1000,
            wait_ipc=True,
        )

    async def _teardown(self):
        if self.text_publisher:
            await self.text_publisher.stop()
        if self.audio_subscriber:
            await self.audio_subscriber.stop()

    async def send_test_text(self):
        """Send SENTENCE_START -> text -> SENTENCE_END sequence."""
        sequence = [
            "SENTENCE_START",
            self.text,
            "SENTENCE_END",
        ]
        for item in sequence:
            payload = {
                "text": item,
                "timestamp": time.time(),
                "source": "tts_smoke_tester",
            }
            await self.text_publisher.send_json(payload)
            await asyncio.sleep(0.1)

    async def collect_audio(self) -> bytes:
        """Listen for PCM audio chunks until the final flag or timeout."""
        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            message = await self.audio_subscriber.recv_json()
            if not message:
                await asyncio.sleep(0.05)
                continue

            audio_hex = message.get("audio_data")
            metadata = message.get("metadata") or {}
            if audio_hex:
                self.audio_buffer.extend(bytes.fromhex(audio_hex))
            if not self.session_id:
                self.session_id = metadata.get("session_id")

            if metadata.get("end_of_stream"):
                break

        if not self.audio_buffer:
            raise RuntimeError("未在超时时间内收到任何音频数据")

        return bytes(self.audio_buffer)

    def save_as_mp3(self, pcm_bytes: bytes) -> Path:
        """Convert collected PCM16 audio to MP3."""
        if AudioSegment is None:
            raise RuntimeError(
                "缺少 pydub 依赖。请先运行 `pip install pydub` 并确保系统可用 ffmpeg。"
            )

        segment = AudioSegment(
            data=pcm_bytes,
            sample_width=2,
            frame_rate=16000,
            channels=1,
        )

        session_suffix = self.session_id or f"tts_test_{int(time.time())}"
        output_path = self.output_dir / f"{session_suffix}.mp3"
        segment.export(output_path, format="mp3")
        return output_path


async def main(args):
    output_dir = Path(args.output_dir).expanduser().resolve()

    async with TTSSmokeTester(
        text=args.text,
        output_dir=output_dir,
        timeout=args.timeout,
    ) as tester:
        await tester.send_test_text()
        pcm_audio = await tester.collect_audio()
        mp3_path = tester.save_as_mp3(pcm_audio)
        print(f"✅ 成功生成音频: {mp3_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="向 TTS 服务发送测试文本并保存返回的音频（MP3）"
    )
    parser.add_argument(
        "--text",
        default="你好，这是一个 TTS 服务连通性测试。",
        help="要合成的测试文本内容",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "examples" / "tts_outputs"),
        help="保存 MP3 文件的目录",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="等待音频返回的超时时间（秒）",
    )

    asyncio.run(main(parser.parse_args()))

