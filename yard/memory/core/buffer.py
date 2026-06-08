"""按 thread_id 缓存近期对话，供心跳批量写入 Mem0。"""

from __future__ import annotations

from collections import deque
from typing import Any


def _message_role_and_content(message: Any) -> tuple[str, str] | None:
    msg_type = getattr(message, "type", None)
    if msg_type == "human":
        role = "user"
    elif msg_type in ("ai", "assistant"):
        role = "assistant"
    else:
        return None
    content = getattr(message, "content", "")
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        content = "\n".join(p for p in parts if p)
    text = str(content or "").strip()
    if not text:
        return None
    return role, text


class SessionBuffer:
    """按 LangGraph messages 列表下标增量缓存；flush 后保留 _seen_len 避免重复 append。"""

    def __init__(self, *, max_messages_per_thread: int = 200) -> None:
        self._maxlen = max_messages_per_thread
        self._buffers: dict[str, deque[dict[str, str]]] = {}
        # 已纳入 buffer 或已 flush 的 messages 列表长度（水位线，flush 后不重置）
        self._seen_len: dict[str, int] = {}

    def append_from_state(self, thread_id: str, messages: list[Any]) -> None:
        if not thread_id:
            thread_id = "default"
        if thread_id not in self._buffers:
            self._buffers[thread_id] = deque(maxlen=self._maxlen)
            self._seen_len.setdefault(thread_id, 0)

        seen = self._seen_len[thread_id]
        # 摘要/压缩后 checkpoint messages 变短，已 flush 的旧下标失效，从 0 重新对齐
        if len(messages) < seen:
            seen = 0
        buf = self._buffers[thread_id]
        for msg in messages[seen:]:
            parsed = _message_role_and_content(msg)
            if parsed:
                role, text = parsed
                buf.append({"role": role, "content": text})
        self._seen_len[thread_id] = len(messages)

    def flush_thread(self, thread_id: str) -> list[dict[str, str]]:
        """写入 Mem0 后清空待发送队列，但保留 _seen_len 水位线。"""
        buf = self._buffers.pop(thread_id, None)
        if not buf:
            return []
        return list(buf)

    def flush_all(self) -> dict[str, list[dict[str, str]]]:
        out: dict[str, list[dict[str, str]]] = {}
        for tid in list(self._buffers.keys()):
            msgs = self.flush_thread(tid)
            if msgs:
                out[tid] = msgs
        return out

    def has_pending(self) -> bool:
        return any(len(b) > 0 for b in self._buffers.values())

    def clear_all(self) -> None:
        self._buffers.clear()
        self._seen_len.clear()

    def clear_thread(self, thread_id: str) -> None:
        if not thread_id:
            return
        self._buffers.pop(thread_id, None)
        self._seen_len.pop(thread_id, None)
