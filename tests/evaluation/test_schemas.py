import pytest
from pydantic import ValidationError

from src.eval_api.schemas import (
    AgentAffectSnapshot,
    EmotionEvalRequest,
    EmotionEvalResponse,
    EmotionMetricScore,
    EmotionTurnResult,
    EvalSummary,
)


def test_request_defaults_to_five_rounds() -> None:
    request = EmotionEvalRequest(
        background="独居，最近工作压力大",
        initial_mood="anxious",
    )

    assert request.rounds == 5
    assert request.goal == "评估 agent 的情绪支持质量"


def test_request_rejects_too_many_rounds() -> None:
    with pytest.raises(ValidationError):
        EmotionEvalRequest(
            background="独居，最近工作压力大",
            initial_mood="anxious",
            rounds=9,
        )


def test_response_serializes_completed_result() -> None:
    response = EmotionEvalResponse(
        session_id="eval_test",
        status="completed",
        scenario=EmotionEvalRequest(background="背景", initial_mood="sad"),
        turns=[
            EmotionTurnResult(
                round=1,
                user="我最近睡不好。",
                assistant="听起来你最近一直很累。",
                agent_affect=AgentAffectSnapshot(
                    emotion="neutral",
                    vad={"v": 0.1, "a": 0.2, "d": 0.0},
                    relationship_stage="acquaintance",
                ),
            )
        ],
        scores=[
            EmotionMetricScore(
                name="empathy",
                score=0.8,
                reason="回应了用户情绪。",
                evidence=["第 1 轮复述了用户的疲惫。"],
            )
        ],
        summary=EvalSummary(
            overall_score=0.8,
            verdict="pass",
            conclusion="情绪支持稳定。",
            improvement_suggestions=["减少模板化表达。"],
        ),
    )

    data = response.model_dump()

    assert data["status"] == "completed"
    assert data["turns"][0]["agent_affect"]["emotion"] == "neutral"
