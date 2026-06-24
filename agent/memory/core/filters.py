"""Mem0 写入价值过滤器：纯函数，无 LLM 调用，0 延迟。"""
from __future__ import annotations

import re

# 纯问候/心跳匹配：这类消息无记忆价值
_GREETING_RE = re.compile(
    r"^(嗯+|哦+|啊+|好的?|好吧|呢|哈{1,3}|嗯嗯|ok|okay|yeah|yep|mm+|hmm+|"
    r"hi|hey|hello|bye|拜拜|再见|谢谢|谢了|感谢|thx|thanks)[.!?。！？\s]*$",
    re.IGNORECASE,
)

# 最小字符数：低于此值直接跳过（避免单字/标点触发 infer）
_MIN_CHARS = 8


def _single_has_value(text: str) -> bool:
    """判断单条用户消息是否有记忆价值。"""
    t = (text or "").strip()
    if not t:
        return False
    if len(t) < _MIN_CHARS:
        return False
    if _GREETING_RE.match(t):
        return False
    return True


def has_memory_value(messages: list[dict[str, str]]) -> bool:
    """判断一批对话消息是否值得调用 Mem0 LLM infer 提取记忆。

    任意一条用户消息有价值即返回 True；全部无价值或无用户消息则返回 False。
    内部异常时保守返回 True（避免漏记）。
    """
    try:
        user_texts = [
            m["content"]
            for m in messages
            if m.get("role") == "user" and m.get("content")
        ]
        if not user_texts:
            return False
        return any(_single_has_value(t) for t in user_texts)
    except Exception:
        return True
