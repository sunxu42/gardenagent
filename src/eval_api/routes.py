from __future__ import annotations

from collections.abc import Mapping
from json import JSONDecodeError

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from src.eval_api.schemas import EmotionEvalRequest, EmotionEvalResponse, EvalError


def _cors_headers() -> dict[str, str]:
    """Return CORS headers for eval POST and OPTIONS requests."""

    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _json(
    payload: BaseModel | Mapping[str, object],
    status: int = 200,
) -> JSONResponse:
    """Return a JSON response with eval API CORS headers."""

    content = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    return JSONResponse(content, status_code=status, headers=_cors_headers())


async def _options(_request: Request) -> Response:
    """Handle eval API CORS preflight requests."""

    return Response(status_code=204, headers=_cors_headers())


async def run_emotion_eval(request: EmotionEvalRequest) -> EmotionEvalResponse:
    """Run one emotion-support evaluation with production dependencies."""

    from src.evaluation.agent_client import YardAgentClient
    from src.evaluation.emotion_metrics import EmotionSupportEvaluator
    from src.evaluation.session import EvalSession
    from src.evaluation.simulated_user import SimulatedUser
    from yard.configs.resolve import resolve_yard_runtime
    from yard.configs.secrets import load_secrets
    from yard.configs.settings import load_settings

    settings = load_settings()
    config = resolve_yard_runtime(settings, load_secrets())
    simulated_user = SimulatedUser.from_config(config)
    agent_client = await YardAgentClient.create()
    session = EvalSession(
        simulated_user=simulated_user,
        agent_client=agent_client,
        evaluator=EmotionSupportEvaluator.from_config(config),
    )
    return await session.run(request)


async def post_emotion_support_run(request: Request) -> JSONResponse:
    """Validate an evaluation request and run the emotion-support session."""

    try:
        payload = await request.json()
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return _json(
            _failed_response("invalid_json", f"Invalid JSON request body: {exc}"),
            status=400,
        )

    try:
        eval_request = EmotionEvalRequest.model_validate(payload)
    except ValidationError as exc:
        return _json(
            _failed_response("validation_error", exc.errors()),
            status=400,
        )

    try:
        result = await run_emotion_eval(eval_request)
    except Exception as exc:
        return _json(
            _failed_response("eval_run_failed", str(exc)),
            status=500,
        )

    return _json(result, status=200 if result.status == "completed" else 500)


def create_eval_routes() -> list[Route]:
    """Create Starlette routes for the eval HTTP API."""

    return [
        Route("/api/eval/emotion-support/run", post_emotion_support_run, methods=["POST"]),
        Route("/api/eval/emotion-support/run", _options, methods=["OPTIONS"]),
    ]


def _failed_response(code: str, message: object) -> EmotionEvalResponse:
    return EmotionEvalResponse(
        session_id="",
        status="failed",
        error=EvalError(
            code=code,
            message=str(message),
        ),
    )
