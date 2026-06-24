"""本轮策略标签：供 Prompt 与 TTS 统一消费。"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from agent.emotion.core.policy import EmpathyMode, ResponsePolicy, Stance


@dataclass(frozen=True)
class StrategyTags:
    mode: str
    voice_style: str
    length: str
    llm_guideline: str
    tts_profile: str

    def as_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}


_MODE_LABELS: dict[str, str] = {
    "de_escalation": "缓和对抗",
    "listen": "深度倾听",
    "celebrate": "分享喜悦",
    "balanced": "自然对话",
}

_VOICE_LABELS: dict[str, str] = {
    "steady": "沉稳",
    "soft": "柔软",
    "bright": "明亮",
    "warm": "亲切",
}

_LENGTH_GUIDELINES: dict[str, str] = {
    "short": "单轮不超过 2 句、40 字以内；禁止说教或列清单。",
    "medium": "单轮 2～4 句，保持口语化，一次只谈一件事。",
}


def derive_strategy_tags(
    policy: ResponsePolicy,
    *,
    user_emotion: str = "neutral",
) -> StrategyTags:
    """由 ResponsePolicy 映射为扁平策略标签。"""
    mode, voice_style, length, tts_profile = _resolve_axes(policy, user_emotion)
    guideline = _build_llm_guideline(policy, mode, voice_style, length)
    return StrategyTags(
        mode=mode,
        voice_style=voice_style,
        length=length,
        llm_guideline=guideline,
        tts_profile=tts_profile,
    )


def _resolve_axes(
    policy: ResponsePolicy,
    user_emotion: str,
) -> tuple[str, str, str, str]:
    empathy: EmpathyMode = policy.empathy_mode
    stance: Stance = policy.stance

    if empathy == "de_escalate":
        return "de_escalation", "steady", "short", "calm_steady"
    if empathy in ("mirror_warmth", "acknowledge_first"):
        return "listen", "soft", "short", "warm_comfort"
    if empathy == "celebrate_with":
        return "celebrate", "bright", "medium", "cheerful_light"

    if user_emotion in {"sad", "fear", "angry"}:
        return "listen", "soft", "short", "warm_comfort"
    if user_emotion == "happy":
        return "celebrate", "bright", "medium", "cheerful_light"

    if stance == "guarded_formal":
        return "balanced", "steady", "medium", "neutral_warm"
    if stance == "warm_casual":
        return "balanced", "warm", "medium", "neutral_warm"
    return "balanced", "warm", "medium", "neutral_warm"


def _build_llm_guideline(
    policy: ResponsePolicy,
    mode: str,
    voice_style: str,
    length: str,
) -> str:
    mode_zh = _MODE_LABELS.get(mode, mode)
    voice_zh = _VOICE_LABELS.get(voice_style, voice_style)
    length_rule = _LENGTH_GUIDELINES.get(length, _LENGTH_GUIDELINES["medium"])
    repair = ""
    if policy.repair_action == "apologize_if_mistake":
        repair = "如有误会先简短致歉。"
    elif policy.repair_action == "clarify_before_advise":
        repair = "给建议前先澄清用户真正在意的事。"
    return f"本轮模式：{mode_zh}；语气：{voice_zh}。{length_rule}{repair}"


def strategy_tags_summary(tags: StrategyTags | None) -> str:
    if tags is None:
        return ""
    mode_zh = _MODE_LABELS.get(tags.mode, tags.mode)
    voice_zh = _VOICE_LABELS.get(tags.voice_style, tags.voice_style)
    length_zh = "短句" if tags.length == "short" else "适中"
    return f"{mode_zh} · {voice_zh} · {length_zh}"
