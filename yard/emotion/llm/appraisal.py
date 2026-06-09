"""用户话 → VAD：glm-4.7-flash 前置判定（与主对话模型分离，共用 API Key）。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, Field

from yard.configs.config import Config
from yard.emotion.constants import EMOTION_APPRAISAL_TEMPERATURE
from yard.emotion.core.policy import TurnAppraisalV2
from yard.emotion.core.service import EmotionService
from yard.emotion.core.vad import VAD

# V1 legacy：直接估计「助手回复时应处的 VAD」；运行时已固定走 v2。
APPRAISAL_SYSTEM_PROMPT = """你是语音助手的情绪评估器。根据用户最新一句话，估计助手在回复时应处的 VAD 状态（不是用户的情绪）。

坐标含义：
- v (valence): [-1, 1]，越高越积极
- a (arousal): [0, 1]，越高越激动
- d (dominance): [-1, 1]，越高越有掌控感

参考原型（仅供对齐，可输出中间值）：
happy (0.8, 0.7, 0.5), surprised (0.1, 0.8, -0.1), neutral (0.0, 0.3, 0.0),
sad (-0.7, 0.3, -0.5), fear (-0.6, 0.8, -0.7), angry (-0.6, 0.8, 0.6), hate (-0.7, 0.5, 0.2)

规则：
- 用户开心/分享好事 → 助手偏 happy；用户难过 → 偏 sad；用户愤怒 → 偏 angry 但克制；用户害怕 → 偏 fear 且安抚
- 纯信息问答、中性 → 接近 neutral
- weight: [0, 1]，本轮情绪偏移强度；平淡对话 0.2~0.4，强情绪场景 0.6~0.9

只输出一个“纯 JSON 对象”，不使用任何 Markdown。
禁止使用 ``` 或 ```json 代码块、禁止用反引号包裹。
输出必须以 `{` 开头，并以 `}` 结尾；中间不要有任何其它字符或解释。"""

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


class VadAppraisalResult(BaseModel):
    v: float = Field(ge=-1.0, le=1.0, description="valence")
    a: float = Field(ge=0.0, le=1.0, description="arousal")
    d: float = Field(ge=-1.0, le=1.0, description="dominance")
    weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="appraisal pull strength toward target VAD",
    )


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
        service: EmotionService,
        *,
        max_user_chars: int = 2000,
    ) -> None:
        self._service = service
        self._max_user_chars = max(200, max_user_chars)
        self._structured = llm.with_structured_output(VadAppraisalResult)
        self._structured_v2 = llm.with_structured_output(TurnAppraisalV2)
        self._fallback = llm

    def _messages(self, user_text: str) -> list:
        clipped = user_text.strip()[: self._max_user_chars]
        return [
            SystemMessage(content=APPRAISAL_SYSTEM_PROMPT),
            HumanMessage(content=clipped),
        ]

    def _messages_v2(self, user_text: str) -> list:
        clipped = user_text.strip()[: self._max_user_chars]
        return [
            SystemMessage(content=APPRAISAL_V2_SYSTEM_PROMPT),
            HumanMessage(content=clipped),
        ]

    def _parse_result(self, raw: Any) -> VadAppraisalResult | None:
        if isinstance(raw, VadAppraisalResult):
            return raw
        if isinstance(raw, dict):
            try:
                return VadAppraisalResult.model_validate(raw)
            except Exception:
                return None
        if hasattr(raw, "content"):
            return self._parse_result(getattr(raw, "content", ""))
        if isinstance(raw, str):
            data = _extract_json_object(raw)
            if data:
                try:
                    return VadAppraisalResult.model_validate(data)
                except Exception:
                    return None
        return None

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

    def _apply(self, result: VadAppraisalResult) -> VAD:
        target = VAD(result.v, result.a, result.d).clamp()
        weight = max(0.0, min(1.0, float(result.weight)))
        self._service.mark_last_appraisal(target, weight)
        vad = self._service.apply(target, weight=weight, source="appraisal")
        logger.debug(
            "emotion.appraisal target={} weight={} -> {}",
            target.as_dict(),
            weight,
            vad.as_dict(),
        )
        return vad

    def appraise_and_apply(self, user_text: str) -> VAD | None:
        text = (user_text or "").strip()
        if not text:
            return None
        try:
            raw = self._structured.invoke(self._messages(text))
            result = self._parse_result(raw)
            if result is None:
                raise ValueError("structured output parse failed")
            return self._apply(result)
        except Exception as e:
            # 结构化输出链路期望“纯 JSON”，但某些模型会回 code fence（```json ... ```）
            # 这类问题会在 fallback 中被正则成功兜底，因此这里做降噪。
            msg = str(e)
            if "json_invalid" in msg or "Invalid JSON" in msg or "expected value" in msg:
                logger.debug("emotion appraisal structured invoke failed (non-JSON wrapper); trying fallback: {}", msg)
            else:
                logger.warning("emotion appraisal structured invoke failed: {!r}; trying fallback", e)
        try:
            resp = self._fallback.invoke(self._messages(text))
            content = resp.content if hasattr(resp, "content") else str(resp)
            result = self._parse_result(content)
            if result is None:
                excerpt = (content or "").replace("\n", " ").strip()
                logger.warning("emotion appraisal fallback could not parse: {}", excerpt[:300])
                return None
            return self._apply(result)
        except Exception as e:
            logger.warning("emotion appraisal failed: {!r}", e)
            return None

    async def appraise_and_apply_async(self, user_text: str) -> VAD | None:
        text = (user_text or "").strip()
        if not text:
            return None
        try:
            raw = await self._structured.ainvoke(self._messages(text))
            result = self._parse_result(raw)
            if result is None:
                raise ValueError("structured output parse failed")
            return self._apply(result)
        except Exception as e:
            msg = str(e)
            if "json_invalid" in msg or "Invalid JSON" in msg or "expected value" in msg:
                logger.debug("emotion appraisal structured ainvoke failed (non-JSON wrapper); trying fallback: {}", msg)
            else:
                logger.warning("emotion appraisal structured ainvoke failed: {!r}; trying fallback", e)
        try:
            resp = await self._fallback.ainvoke(self._messages(text))
            content = resp.content if hasattr(resp, "content") else str(resp)
            result = self._parse_result(content)
            if result is None:
                excerpt = (content or "").replace("\n", " ").strip()
                logger.warning("emotion appraisal fallback could not parse: {}", excerpt[:300])
                return None
            return self._apply(result)
        except Exception as e:
            logger.warning("emotion appraisal failed: {!r}", e)
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
