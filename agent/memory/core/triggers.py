"""中英文显式「记住」触发检测与 fact 抽取（纯函数）。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence


DEFAULT_KEYWORDS_ZH: tuple[str, ...] = (
    "记住",
    "别忘了",
    "不要忘记",
    "请记住",
    "帮我记住",
    "帮我记一下",
    "记一下",
    "记下来",
    "记入记忆",
    "写入记忆",
    "保存到记忆",
    "存一下",
    "以后要记得",
    "下次记得",
    "你得记住",
    "需要记住",
    "务必记住",
    "一定记住",
    "可别忘了",
)

DEFAULT_KEYWORDS_EN: tuple[str, ...] = (
    "remember",
    "don't forget",
    "do not forget",
    "never forget",
    "keep in mind",
    "bear in mind",
    "note that",
    "noted that",
    "store this",
    "save this",
    "save to memory",
    "add to memory",
    "memorize",
    "memorise",
    "please remember",
    "remember that",
    "don't forget that",
    "for future reference",
    "worth remembering",
    "make a note",
)

DEFAULT_NEGATIVE_PATTERNS: tuple[str, ...] = (
    r"还记得|记得吗|没忘|忘记了吗|想起来|回忆一下|记日记|写日志",
    r"(?i)\b(do you|did you|can you)\s+remember\b",
    r"(?i)\bremember\s+(when|how|that time)\b",
    r"(?i)\b(I|you)\s+remember\b",
)

_WEAK_ZH_PATTERN = re.compile(r"^记着[^，。！？\s]*")
_POLITE_PREFIX_ZH = re.compile(r"^(请|帮我)\s*")
_POLITE_PREFIX_EN = re.compile(r"^(please|could you)\s+", re.IGNORECASE)
_LEADING_PUNCT = re.compile(r"^[\s:：,，、\-—]+")


@dataclass
class ExplicitTriggerConfig:
    enabled: bool = True
    keywords_zh: Sequence[str] = field(default_factory=lambda: list(DEFAULT_KEYWORDS_ZH))
    keywords_en: Sequence[str] = field(default_factory=lambda: list(DEFAULT_KEYWORDS_EN))
    negative_patterns: Sequence[str] = field(default_factory=lambda: list(DEFAULT_NEGATIVE_PATTERNS))
    weak_zh_enabled: bool = False
    weak_en_enabled: bool = False


@dataclass(frozen=True)
class ExplicitRememberMatch:
    fact_text: str
    trigger: str
    language: str  # "zh" | "en" | "weak_zh"


def _compile_negative(patterns: Sequence[str]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except re.error:
            continue
    return compiled


def _matches_negative(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in patterns)


def _find_zh_trigger(text: str, keywords: Sequence[str]) -> str | None:
    for kw in sorted(keywords, key=len, reverse=True):
        if kw and kw in text:
            return kw
    return None


def _find_en_trigger(text: str, keywords: Sequence[str]) -> str | None:
    lower = text.lower()
    for phrase in sorted(keywords, key=len, reverse=True):
        if not phrase:
            continue
        if " " in phrase or "'" in phrase:
            if phrase.lower() in lower:
                return phrase
        else:
            if re.search(rf"\b{re.escape(phrase)}\b", lower):
                return phrase
    return None


def extract_fact_text(user_text: str, trigger: str) -> str:
    """去掉触发语与礼貌前缀，得到待写入 fact。"""
    text = user_text
    if trigger:
        idx = text.lower().find(trigger.lower()) if trigger.isascii() else text.find(trigger)
        if idx >= 0:
            text = text[:idx] + text[idx + len(trigger) :]
    text = _LEADING_PUNCT.sub("", text.strip())
    text = _POLITE_PREFIX_ZH.sub("", text)
    text = _POLITE_PREFIX_EN.sub("", text).strip()
    if text.lower().startswith("that "):
        text = text[5:].strip()
    if len(text) < 2:
        return user_text.strip()
    return text


def detect_explicit_remember(
    user_text: str,
    config: ExplicitTriggerConfig | None = None,
) -> ExplicitRememberMatch | None:
    """检测用户是否显式要求记住；命中否定模式则返回 None。"""
    if not user_text or not user_text.strip():
        return None
    cfg = config or ExplicitTriggerConfig()
    if not cfg.enabled:
        return None

    text = user_text.strip()
    negatives = _compile_negative(cfg.negative_patterns)
    if _matches_negative(text, negatives):
        return None

    trigger = _find_zh_trigger(text, cfg.keywords_zh)
    if trigger:
        return ExplicitRememberMatch(
            fact_text=extract_fact_text(text, trigger),
            trigger=trigger,
            language="zh",
        )

    trigger = _find_en_trigger(text, cfg.keywords_en)
    if trigger:
        return ExplicitRememberMatch(
            fact_text=extract_fact_text(text, trigger),
            trigger=trigger,
            language="en",
        )

    if cfg.weak_zh_enabled and _WEAK_ZH_PATTERN.search(text):
        return ExplicitRememberMatch(
            fact_text=text,
            trigger="weak_zh",
            language="weak_zh",
        )

    return None
