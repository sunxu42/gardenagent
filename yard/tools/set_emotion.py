"""set_emotion 工具：LLM 每轮自评当前应有的情绪，写入 EmotionService（影响下一轮）。"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

from yard.emotion.core.service import EmotionService
from yard.emotion.core.vad import EMOTION_PROTOTYPES


class SetEmotionInput(BaseModel):
    emotion: str = Field(
        description="本轮应表现的情绪，取值之一：happy/sad/angry/fear/hate/surprised/neutral",
    )
    intensity: int = Field(
        default=3,
        description="情绪强度 1~5（1 最弱，5 最强）",
    )
    reason: str = Field(default="", description="一句话说明依据（可选）")


def create_set_emotion_tool(service: EmotionService) -> StructuredTool:
    async def set_emotion(emotion: str, intensity: int = 3, reason: str = "") -> dict[str, Any]:
        key = (emotion or "").strip().lower()
        if key not in EMOTION_PROTOTYPES:
            return {"ok": False, "error": f"unknown emotion: {emotion!r}"}
        intensity = max(1, min(5, int(intensity)))
        target = EMOTION_PROTOTYPES[key]
        weight = intensity / 5.0
        try:
            vad = service.apply(target, weight=weight, source="llm")
            logger.debug("set_emotion {} x{} ({}) -> {}", key, intensity, reason, vad.as_dict())
            return {"ok": True, "emotion": key, "intensity": intensity}
        except Exception as e:
            logger.warning("set_emotion failed: {!r}", e)
            return {"ok": False, "error": repr(e)}

    return StructuredTool.from_function(
        name="set_emotion",
        description=(
            "评估并设置助手当前应表现的情绪。每轮回复时调用一次："
            "根据用户状态、对话目标与刚发生的事，选 happy/sad/angry/fear/hate/surprised/neutral 之一与强度。"
            "此调用不发声，仅调节后续语气，请勿在口播文本里复述。"
        ),
        coroutine=set_emotion,
        args_schema=SetEmotionInput,
    )
