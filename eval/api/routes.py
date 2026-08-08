from __future__ import annotations

from collections.abc import Mapping, Sequence
from json import JSONDecodeError
from pathlib import Path

from eval.api.response_cache import StampCache, directory_content_stamp
from shared.config.paths import resolve_eval_runs_dir, resolve_eval_scenarios_dir

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from eval.api.schemas import (
    CoverageCellDTO,
    CoverageMatrixDTO,
    CoverageScenarioRefDTO,
    EmotionEvalRequest,
    EmotionEvalResponse,
    EmotionSupportRunRequest,
    EvalError,
    EvalRunCancelResponse,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunStartedResponse,
    EvalRunSummary,
    ScenarioEvalRequest,
    ScenarioSummary,
)
from eval.api.mapping import to_eval_run_response, to_eval_run_response_from_record
from eval.application.job_manager import EvalJobConflictError, EvalJobManager
from eval.infrastructure.persistence import list_run_summaries, load_run_record
from eval.domain.scenario import (
    iter_scenario_yaml_paths,
    load_scenario,
    list_scenarios_with_paths,
    resolve_scenario_by_id,
)


def _cors_headers() -> dict[str, str]:
    """Return CORS headers for eval API requests."""

    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _json(
    payload: BaseModel | Mapping[str, object] | Sequence[object],
    status: int = 200,
) -> JSONResponse:
    """Return a JSON response with eval API CORS headers."""

    if isinstance(payload, BaseModel):
        content: object = payload.model_dump(mode="json")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        content = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in payload
        ]
    else:
        content = payload
    return JSONResponse(content, status_code=status, headers=_cors_headers())


async def _options(_request: Request) -> Response:
    """Handle eval API CORS preflight requests."""

    return Response(status_code=204, headers=_cors_headers())


async def run_emotion_eval(request: EmotionEvalRequest) -> EmotionEvalResponse:
    """Run one emotion-support evaluation with production dependencies."""

    from eval.application.agent_client import EvalAgentClient
    from eval.domain.emotion_metrics import EmotionSupportEvaluator
    from eval.domain.session import EvalSession
    from eval.domain.simulated_user import SimulatedUser
    from shared.config.resolve_agent import resolve_agent_runtime
    from shared.config.secrets import load_secrets
    from shared.config.agent import load_agent_settings

    settings = load_agent_settings()
    config = resolve_agent_runtime(settings, load_secrets())
    simulated_user = SimulatedUser.from_config(config)
    agent_client = await EvalAgentClient.create()
    session = EvalSession(
        simulated_user=simulated_user,
        agent_client=agent_client,
        evaluator=EmotionSupportEvaluator.from_config(config),
    )
    return await session.run(request)


async def run_scenario_eval(request: ScenarioEvalRequest) -> EvalRunResponse:
    """Run one scripted scenario evaluation."""

    from eval.application.agent_pool import EvalAgentFactory
    from eval.domain.judge.model_factory import build_eval_model
    from eval.domain.judge.runner import JudgeRunner
    from eval.domain.runner import EvalRunner
    from shared.config.resolve_agent import resolve_agent_runtime
    from shared.config.secrets import load_secrets
    from shared.config.agent import load_agent_settings

    scenario = resolve_scenario_by_id(request.scenario_id)
    judge_runner = None
    if scenario.judge is not None and scenario.judge.enabled:
        config = resolve_agent_runtime(load_agent_settings(), load_secrets())
        judge_runner = JudgeRunner(build_eval_model(config))

    async with EvalAgentFactory.run_guard():
        agent_client = await EvalAgentFactory.create_client()
        try:
            result = await EvalRunner(
                agent_client=agent_client,
                judge_runner=judge_runner,
            ).run_scenario(scenario, persist=request.persist)
        finally:
            await agent_client.aclose()
    return to_eval_run_response(result)


async def run_eval(request: EvalRunRequest) -> EvalRunResponse:
    """Dispatch a unified evaluation request."""

    if request.mode == "scenario":
        if not request.scenario_id:
            raise ValueError("scenario_id is required for scenario mode")
        return await run_scenario_eval(
            ScenarioEvalRequest(scenario_id=request.scenario_id, persist=request.persist),
        )

    if request.exploratory is None:
        raise ValueError("exploratory payload is required for exploratory mode")

    emotion_result = await run_emotion_eval(request.exploratory)
    return EvalRunResponse(
        run_id=emotion_result.session_id,
        mode="exploratory",
        tier="exploratory",
        status=emotion_result.status,
        observations=emotion_result.turns,
        scores=emotion_result.scores,
        summary=emotion_result.summary,
        judge=[
        ],
        error=emotion_result.error,
    )


_scenario_summaries_cache: StampCache[list[ScenarioSummary]] = StampCache(ttl_seconds=30.0)
_coverage_cache: StampCache[CoverageMatrixDTO] = StampCache(ttl_seconds=15.0)
_run_summaries_cache: StampCache[list[dict[str, object]]] = StampCache(ttl_seconds=15.0)


def _scenario_dir_stamp(root: Path) -> float:
    return directory_content_stamp(root, "**/*.yaml")


def _runs_dir_stamp() -> float:
    return directory_content_stamp(resolve_eval_runs_dir(), "eval_*.json")


def _build_all_scenario_summaries(root: Path) -> list[ScenarioSummary]:
    summaries: list[ScenarioSummary] = []
    for path in iter_scenario_yaml_paths(root):
        scenario = load_scenario(path)
        summaries.append(
            ScenarioSummary(
                id=str(path.relative_to(root)).replace("\\", "/").removesuffix(".yaml"),
                description=scenario.description,
                domain=scenario.domain,
                tier=scenario.tier,
                tags=scenario.tags,
            )
        )
    return summaries


def list_scenario_summaries(tier: str | None = None) -> list[ScenarioSummary]:
    """List available scenario fixtures."""

    root = resolve_eval_scenarios_dir()
    stamp = _scenario_dir_stamp(root)
    all_summaries = _scenario_summaries_cache.get(
        (stamp,),
        lambda: _build_all_scenario_summaries(root),
    )
    if not tier:
        return all_summaries
    return [item for item in all_summaries if item.tier == tier]


def _cached_run_summary_rows() -> list[dict[str, object]]:
    stamp = _runs_dir_stamp()
    return _run_summaries_cache.get(
        (stamp,),
        lambda: list_run_summaries(limit=200),
    )


def build_coverage_response(
    *,
    tier: str | None = None,
    domain: str | None = None,
) -> CoverageMatrixDTO:
    """Build coverage matrix DTO from fixtures and persisted runs."""

    stamps = (
        _scenario_dir_stamp(resolve_eval_scenarios_dir()),
        _runs_dir_stamp(),
        tier or "",
        domain or "",
    )
    return _coverage_cache.get(
        stamps,
        lambda: _build_coverage_response_uncached(tier=tier, domain=domain),
    )


def _build_coverage_response_uncached(
    *,
    tier: str | None = None,
    domain: str | None = None,
) -> CoverageMatrixDTO:
    """Build coverage matrix DTO without response caching."""

    from eval.domain.coverage import ScenarioRunSnapshot, build_coverage_matrix, runs_from_summaries
    from eval.domain.taxonomy import get_taxonomy_registry

    root = resolve_eval_scenarios_dir()
    loaded = list_scenarios_with_paths(root)
    runs = runs_from_summaries(_cached_run_summary_rows())
    matrix = build_coverage_matrix(
        loaded_scenarios=loaded,
        runs=runs,
        registry=get_taxonomy_registry(),
    )

    latest_runs: dict[tuple[str, str], ScenarioRunSnapshot] = {}
    for run in runs:
        key = (run.scenario_id.replace("\\", "/").strip("/"), run.tier)
        existing = latest_runs.get(key)
        if existing is None or (run.finished_at or "") >= (existing.finished_at or ""):
            latest_runs[key] = run

    cells: list[CoverageCellDTO] = []
    for cell in matrix.cells:
        if tier and cell.tier != tier:
            continue
        if domain and cell.domain != domain:
            continue
        scenario_rows: list[CoverageScenarioRefDTO] = []
        for ref in cell.scenarios:
            short_id = ref.id.split("/")[-1]
            run = latest_runs.get((ref.id, cell.tier))
            if run is None:
                run = latest_runs.get((short_id, cell.tier))
            scenario_rows.append(
                CoverageScenarioRefDTO(
                    id=ref.id,
                    description=ref.description,
                    tags=list(ref.tags),
                    last_status=run.status if run is not None else None,
                    last_passed=run.passed if run is not None else None,
                )
            )
        cells.append(
            CoverageCellDTO(
                domain=cell.domain,
                domain_label=cell.domain_label,
                tier=cell.tier,
                scenario_count=cell.scenario_count,
                scenarios=scenario_rows,
                tags_covered=list(cell.tags_covered),
                tags_expected=list(cell.tags_expected),
                tags_missing=list(cell.tags_missing),
                tier_expected=cell.tier_expected,
                last_run_at=cell.last_run_at,
                pass_count=cell.pass_count,
                fail_count=cell.fail_count,
                pass_rate=cell.pass_rate,
            )
        )

    return CoverageMatrixDTO(
        generated_at=matrix.generated_at,
        cells=cells,
        tag_coverage=[
            {"tag": row.tag, "scenario_count": row.scenario_count, "domains": list(row.domains)}
            for row in matrix.tag_coverage
        ],
    )


async def get_coverage(request: Request) -> JSONResponse:
    """Return eval coverage matrix."""

    tier = request.query_params.get("tier")
    domain = request.query_params.get("domain")
    return _json(build_coverage_response(tier=tier, domain=domain))


async def get_scenarios(request: Request) -> JSONResponse:
    """Return scenario summaries for the Test panel."""

    tier = request.query_params.get("tier")
    return _json(list_scenario_summaries(tier))


async def post_eval_run(request: Request) -> JSONResponse:
    """Validate and run a unified evaluation request."""

    try:
        payload = await request.json()
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return _json(_failed_run_response("invalid_json", str(exc)), status=400)

    try:
        eval_request = EvalRunRequest.model_validate(payload)
    except ValidationError as exc:
        return _json(_failed_run_response("validation_error", str(exc.errors())), status=400)

    try:
        result = await run_eval(eval_request)
    except Exception as exc:
        return _json(_failed_run_response("eval_run_failed", str(exc)), status=500)

    return _json(result, status=200 if result.status == "completed" else 500)


async def post_scenario_run(request: Request, job_manager: EvalJobManager | None = None) -> JSONResponse:
    """Validate and run one scenario evaluation."""

    try:
        payload = await request.json()
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return _json(_failed_run_response("invalid_json", str(exc)), status=400)

    try:
        eval_request = ScenarioEvalRequest.model_validate(payload)
    except ValidationError as exc:
        return _json(_failed_run_response("validation_error", str(exc.errors())), status=400)

    if eval_request.async_run:
        if job_manager is None:
            return _json(
                _failed_run_response("eval_unavailable", "async eval is not configured"),
                status=500,
            )
        if not eval_request.client_id:
            return _json(
                _failed_run_response("validation_error", "client_id is required for async runs"),
                status=400,
            )
        try:
            scenario = resolve_scenario_by_id(eval_request.scenario_id)
            run_id = await job_manager.start_scenario(
                eval_request.scenario_id,
                eval_request.client_id,
            )
        except EvalJobConflictError as exc:
            return _json(
                _failed_run_response("eval_already_running", str(exc)),
                status=409,
            )
        except Exception as exc:
            return _json(_failed_run_response("eval_run_failed", str(exc)), status=500)

        return _json(
            EvalRunStartedResponse(
                run_id=run_id,
                scenario_id=eval_request.scenario_id,
                tier=scenario.tier,
            ),
            status=202,
        )

    try:
        result = await run_scenario_eval(eval_request)
    except Exception as exc:
        return _json(_failed_run_response("eval_run_failed", str(exc)), status=500)

    return _json(result, status=200 if result.status == "completed" else 500)


async def post_cancel_run(
    request: Request,
    job_manager: EvalJobManager | None = None,
) -> JSONResponse:
    """Cancel one async eval run."""

    if job_manager is None:
        return _json(
            _failed_run_response("eval_unavailable", "async eval is not configured"),
            status=500,
        )
    run_id = request.path_params["run_id"]
    cancelled = await job_manager.cancel(run_id)
    if not cancelled:
        return _json(_failed_run_response("not_found", f"run not found: {run_id}"), status=404)
    return _json(EvalRunCancelResponse(run_id=run_id))


async def get_runs(request: Request) -> JSONResponse:
    """List persisted eval run summaries."""

    limit = int(request.query_params.get("limit", "50"))
    tier = request.query_params.get("tier")
    rows = _cached_run_summary_rows()
    if tier:
        rows = [item for item in rows if item.get("tier") == tier]
    summaries = [
        EvalRunSummary.model_validate(item)
        for item in rows[:limit]
    ]
    return _json(summaries)


async def get_run(request: Request) -> JSONResponse:
    """Return one persisted eval run."""

    run_id = request.path_params["run_id"]
    record = load_run_record(run_id)
    if record is None:
        return _json(_failed_run_response("not_found", f"run not found: {run_id}"), status=404)
    return _json(to_eval_run_response_from_record(record))


async def post_emotion_support_run(
    request: Request,
    job_manager: EvalJobManager | None = None,
) -> JSONResponse:
    """Validate an evaluation request and run the emotion-support session."""

    try:
        payload = await request.json()
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        return _json(
            _failed_emotion_response("invalid_json", f"Invalid JSON request body: {exc}"),
            status=400,
        )

    try:
        run_request = EmotionSupportRunRequest.model_validate(payload)
    except ValidationError as exc:
        return _json(
            _failed_emotion_response("validation_error", exc.errors()),
            status=400,
        )

    eval_request = EmotionEvalRequest.model_validate(
        run_request.model_dump(
            exclude={"client_id", "async_run"},
            by_alias=False,
        )
    )

    if run_request.async_run:
        if job_manager is None:
            return _json(
                _failed_emotion_response("eval_unavailable", "async eval is not configured"),
                status=500,
            )
        if not run_request.client_id:
            return _json(
                _failed_emotion_response("validation_error", "client_id is required for async runs"),
                status=400,
            )
        try:
            run_id = await job_manager.start_exploratory(eval_request, run_request.client_id)
        except EvalJobConflictError as exc:
            return _json(
                _failed_emotion_response("eval_already_running", str(exc)),
                status=409,
            )
        except Exception as exc:
            return _json(_failed_emotion_response("eval_run_failed", str(exc)), status=500)

        return _json(
            EvalRunStartedResponse(
                run_id=run_id,
                scenario_id="exploratory",
                tier="exploratory",
            ),
            status=202,
        )

    try:
        result = await run_emotion_eval(eval_request)
    except Exception as exc:
        return _json(
            _failed_emotion_response("eval_run_failed", str(exc)),
            status=500,
        )

    return _json(result, status=200 if result.status == "completed" else 500)


def create_eval_routes(job_manager: EvalJobManager | None = None) -> list[Route]:
    """Create Starlette routes for the eval HTTP API."""

    async def scenario_run_endpoint(request: Request) -> JSONResponse:
        return await post_scenario_run(request, job_manager=job_manager)

    async def cancel_run_endpoint(request: Request) -> JSONResponse:
        return await post_cancel_run(request, job_manager=job_manager)

    async def emotion_support_run_endpoint(request: Request) -> JSONResponse:
        return await post_emotion_support_run(request, job_manager=job_manager)

    return [
        Route("/api/eval/run", post_eval_run, methods=["POST"]),
        Route("/api/eval/run", _options, methods=["OPTIONS"]),
        Route("/api/eval/scenarios", get_scenarios, methods=["GET"]),
        Route("/api/eval/scenarios", _options, methods=["OPTIONS"]),
        Route("/api/eval/coverage", get_coverage, methods=["GET"]),
        Route("/api/eval/coverage", _options, methods=["OPTIONS"]),
        Route("/api/eval/scenario/run", scenario_run_endpoint, methods=["POST"]),
        Route("/api/eval/scenario/run", _options, methods=["OPTIONS"]),
        Route("/api/eval/runs/{run_id}/cancel", cancel_run_endpoint, methods=["POST"]),
        Route("/api/eval/runs/{run_id}/cancel", _options, methods=["OPTIONS"]),
        Route("/api/eval/runs/{run_id}", get_run, methods=["GET"]),
        Route("/api/eval/runs/{run_id}", _options, methods=["OPTIONS"]),
        Route("/api/eval/runs", get_runs, methods=["GET"]),
        Route("/api/eval/runs", _options, methods=["OPTIONS"]),
        Route("/api/eval/emotion-support/run", emotion_support_run_endpoint, methods=["POST"]),
        Route("/api/eval/emotion-support/run", _options, methods=["OPTIONS"]),
    ]


def _failed_emotion_response(code: str, message: object) -> EmotionEvalResponse:
    return EmotionEvalResponse(
        session_id="",
        status="failed",
        error=EvalError(
            code=code,
            message=str(message),
        ),
    )


def _failed_run_response(code: str, message: object) -> EvalRunResponse:
    return EvalRunResponse(
        run_id="",
        mode="scenario",
        tier="smoke",
        status="failed",
        error=EvalError(code=code, message=str(message)),
    )
