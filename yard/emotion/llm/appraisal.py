"""用户话 → VAD：glm-4.7-flash 前置判定（与主对话模型分离，共用 API Key）。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from yard.configs.config import Config
from yard.emotion.constants import EMOTION_APPRAISAL_TEMPERATURE
from yard.emotion.core.policy import TurnAppraisalV2

APPRAISAL_V2_SYSTEM_PROMPT = """你是语音助手的情绪与关系评估器。根据用户最新一句话，完成两项任务（不是估计助手的情绪）。

坐标含义（用户情绪 VAD）：
- user_v (valence): [-1, 1]，越高越积极
- user_a (arousal): [0, 1]，越高越激动
- user_d (dominance): [-1, 1]，越高越有掌控感

Task 1 — 用户自身情绪（User Affect）：
- 仅估计用户此刻的感受，不是助手的回应情绪
- user_weight: [0, 1]，本轮用户情绪显著度；平淡对话 0.2~0.4，强情绪 0.6~0.9

Task 2 — 对助手的态度变化（Relationship Delta）：
- trust_delta / warmth_delta: 各 ∈ [-0.15, 0.15]，小步增量
- 夸奖、感谢、采纳建议 → trust 或 warmth 上升
- 质疑、指出错误、失望 → trust 下降
- 分享私事、温柔称呼 → warmth 上升
- 辱骂、冷漠拒绝 → warmth 与 trust 下降
- rel_weight: [0, 1]，本轮对关系的影响强度
- interpersonal_cue: 一句中文，描述用户对助手的态度（如「用户在质疑上一轮回答」）

禁止输出助手/agent 的 VAD。只输出一个纯 JSON 对象，无 Markdown 代码块。"""


def create_emotion_appraisal_model(config: Config) -> ChatOpenAI:
    """与主 LLM 共用模型名；Key 可独立配置 emotion_appraisal_api_key。"""
    default_llm_model = Config.model_fields["llm_model_name"].default or "glm-4-flash"
    model_name = (config.llm_model_name or "").strip() or default_llm_model
    return ChatOpenAI(
        model=model_name,
        api_key=config.emotion_appraisal_api_key,
        base_url=config.emotion_appraisal_base_url,
        temperature=EMOTION_APPRAISAL_TEMPERATURE,
        max_tokens=256,
        streaming=False,
        extra_body={"thinking": {"type": "disabled"}},
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


_HEURISTIC_NEUTRAL = frozenset({
    "好", "嗯", "哦", "行", "是", "对", "ok", "OK", "谢谢", "好的", "收到", "明白",
})


def try_heuristic_v2_appraisal(user_text: str) -> TurnAppraisalV2 | None:
    """极短中性句跳过小模型调用。"""
    text = (user_text or "").strip()
    if not text or len(text) > 6:
        return None
    lowered = text.lower()
    if text in _HEURISTIC_NEUTRAL or lowered in _HEURISTIC_NEUTRAL or len(text) <= 2:
        return TurnAppraisalV2(
            user_v=0.0,
            user_a=0.2,
            user_d=0.0,
            user_weight=0.25,
            trust_delta=0.0,
            warmth_delta=0.0,
            rel_weight=0.15,
            interpersonal_cue="用户简短确认或寒暄",
        )
    return None


class EmotionAppraiser:
    def __init__(
        self,
        llm: ChatOpenAI,
        *,
        max_user_chars: int = 2000,
    ) -> None:
        self._max_user_chars = max(200, max_user_chars)
        self._structured_v2 = llm.with_structured_output(TurnAppraisalV2)
        self._fallback = llm

    def _messages_v2(self, user_text: str) -> list:
        clipped = user_text.strip()[: self._max_user_chars]
        return [
            SystemMessage(content=APPRAISAL_V2_SYSTEM_PROMPT),
            HumanMessage(content=clipped),
        ]

    def _parse_v2_result(self, raw: Any) -> TurnAppraisalV2 | None:
        if isinstance(raw, TurnAppraisalV2):
            return raw
        if isinstance(raw, dict):
            try:
                return TurnAppraisalV2.model_validate(raw)
            except Exception:
                return None
        if hasattr(raw, "content"):
            return self._parse_v2_result(getattr(raw, "content", ""))
        if isinstance(raw, str):
            data = _extract_json_object(raw)
            if data:
                try:
                    return TurnAppraisalV2.model_validate(data)
                except Exception:
                    return None
        return None

    def appraise_v2(self, user_text: str) -> TurnAppraisalV2 | None:
        text = (user_text or "").strip()
        if not text:
            return None
        heuristic = try_heuristic_v2_appraisal(text)
        if heuristic is not None:
            return heuristic
        try:
            raw = self._structured_v2.invoke(self._messages_v2(text))
            result = self._parse_v2_result(raw)
            if result is None:
                raise ValueError("structured v2 parse failed")
            return result
        except Exception as e:
            msg = str(e)
            if "json_invalid" not in msg and "Invalid JSON" not in msg:
                logger.warning("emotion appraisal v2 structured failed: {!r}; trying fallback", e)
        try:
            resp = self._fallback.invoke(self._messages_v2(text))
            content = resp.content if hasattr(resp, "content") else str(resp)
            return self._parse_v2_result(content)
        except Exception as e:
            logger.warning("emotion appraisal v2 failed: {!r}", e)
            return None

    async def appraise_v2_async(self, user_text: str) -> TurnAppraisalV2 | None:
        text = (user_text or "").strip()
        if not text:
            return None
        heuristic = try_heuristic_v2_appraisal(text)
        if heuristic is not None:
            return heuristic
        try:
            raw = await self._structured_v2.ainvoke(self._messages_v2(text))
            result = self._parse_v2_result(raw)
            if result is None:
                raise ValueError("structured v2 parse failed")
            return result
        except Exception as e:
            msg = str(e)
            if "json_invalid" not in msg and "Invalid JSON" not in msg:
                logger.warning("emotion appraisal v2 structured failed: {!r}; trying fallback", e)
        try:
            resp = await self._fallback.ainvoke(self._messages_v2(text))
            content = resp.content if hasattr(resp, "content") else str(resp)
            return self._parse_v2_result(content)
        except Exception as e:
            logger.warning("emotion appraisal v2 failed: {!r}", e)
            return None


def user_text_digest(user_text: str) -> str:
    normalized = (user_text or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
