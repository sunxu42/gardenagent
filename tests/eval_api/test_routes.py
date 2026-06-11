from starlette.applications import Starlette
from starlette.testclient import TestClient

from src.eval_api.routes import create_eval_routes
from src.eval_api.schemas import (
    EmotionEvalRequest,
    EmotionEvalResponse,
    EvalError,
    EvalSummary,
)


def test_eval_route_returns_completed_result(monkeypatch) -> None:
    captured_requests: list[EmotionEvalRequest] = []

    async def fake_run_eval(request: EmotionEvalRequest) -> EmotionEvalResponse:
        captured_requests.append(request)
        return EmotionEvalResponse(
            session_id="eval_test",
            status="completed",
            scenario=request,
            turns=[],
            scores=[],
            summary=EvalSummary(
                overall_score=0.8,
                verdict="pass",
                conclusion="ok",
                improvement_suggestions=[],
            ),
        )

    monkeypatch.setattr("src.eval_api.routes.run_emotion_eval", fake_run_eval)

    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.post(
        "/api/eval/emotion-support/run",
        json={"background": "工作压力大", "initial_mood": "anxious", "rounds": 1},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert len(captured_requests) == 1
    assert captured_requests[0].background == "工作压力大"
    assert captured_requests[0].initial_mood == "anxious"
    assert captured_requests[0].rounds == 1


def test_eval_route_returns_failed_result_for_invalid_json() -> None:
    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.post(
        "/api/eval/emotion-support/run",
        content="{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "invalid_json"


def test_eval_route_returns_failed_result_for_validation_error() -> None:
    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.post(
        "/api/eval/emotion-support/run",
        json={"background": "", "initial_mood": "anxious", "rounds": 1},
    )

    assert response.status_code == 400
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "validation_error"


def test_eval_route_options_returns_cors_headers() -> None:
    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.options("/api/eval/emotion-support/run")

    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-methods"] == "POST, OPTIONS"
    assert response.headers["access-control-allow-headers"] == "Content-Type"


def test_eval_route_returns_500_when_eval_fails(monkeypatch) -> None:
    async def fake_run_eval(request: EmotionEvalRequest) -> EmotionEvalResponse:
        return EmotionEvalResponse(
            session_id="eval_failed",
            status="failed",
            scenario=request,
            error=EvalError(
                code="eval_session_failed",
                message="boom",
            ),
        )

    monkeypatch.setattr("src.eval_api.routes.run_emotion_eval", fake_run_eval)

    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.post(
        "/api/eval/emotion-support/run",
        json={"background": "工作压力大", "initial_mood": "anxious", "rounds": 1},
    )

    assert response.status_code == 500
    assert response.json()["status"] == "failed"


def test_eval_route_returns_structured_500_when_eval_raises(monkeypatch) -> None:
    async def fake_run_eval(_request: EmotionEvalRequest) -> EmotionEvalResponse:
        raise RuntimeError("boom")

    monkeypatch.setattr("src.eval_api.routes.run_emotion_eval", fake_run_eval)

    client = TestClient(Starlette(routes=create_eval_routes()))
    response = client.post(
        "/api/eval/emotion-support/run",
        json={"background": "工作压力大", "initial_mood": "anxious", "rounds": 1},
    )

    assert response.status_code == 500
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "eval_run_failed"
    assert "boom" in response.json()["error"]["message"]
