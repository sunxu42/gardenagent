from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from eval.api.schemas import EmotionEvalRequest
from eval.application.agent_pool import EvalAgentPool
from eval.domain.judge.model_factory import build_eval_model
from eval.domain.judge.runner import JudgeRunner
from eval.domain.progress import EvalProgressEvent
from eval.infrastructure.environment import capture_run_environment
from eval.infrastructure.persistence import persist_record_safe
from eval.infrastructure.recorder import RunRecorder
from eval.domain.runner import EvalRunner
from eval.domain.scenario import resolve_scenario_by_id
from eval.domain.session import EvalSession, build_exploratory_record
from eval.application.ports import EvalProgressNotifier
from shared.config.resolve_agent import resolve_agent_runtime
from agent.configs.secrets import load_secrets
from shared.config.agent import load_agent_settings

_log = logging.getLogger(__name__)


class EvalJobConflictError(Exception):
    """Raised when a client already has a running eval job."""

    def __init__(self, client_id: str) -> None:
        super().__init__(f"client already has a running eval: {client_id}")
        self.client_id = client_id


class EvalJobManager:
    """Manage async scenario eval jobs and push progress over WebSocket."""

    def __init__(self, notifier: EvalProgressNotifier) -> None:
        self._notifier = notifier
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._client_active: dict[str, str] = {}
        self._run_clients: dict[str, str] = {}

    def is_running(self, client_id: str) -> bool:
        """Return whether the client currently has an active eval job."""

        return client_id in self._client_active

    async def start_scenario(self, scenario_id: str, client_id: str) -> str:
        """Start one async scenario eval and return the run id immediately."""

        if client_id in self._client_active:
            raise EvalJobConflictError(client_id)

        run_id = f"eval_{uuid4().hex[:12]}"
        cancel_event = asyncio.Event()
        self._cancel_events[run_id] = cancel_event
        self._client_active[client_id] = run_id
        self._run_clients[run_id] = client_id
        asyncio.create_task(
            self._push_setup_progress(
                client_id,
                run_id,
                "评测任务已入队，正在启动…",
            ),
            name=f"eval-ack-{run_id}",
        )
        task = asyncio.create_task(
            self._execute_scenario(run_id, scenario_id, client_id, cancel_event),
            name=f"eval-{run_id}",
        )
        self._tasks[run_id] = task
        return run_id

    async def start_exploratory(self, request: EmotionEvalRequest, client_id: str) -> str:
        """Start one async exploratory eval and return the run id immediately."""

        if client_id in self._client_active:
            raise EvalJobConflictError(client_id)

        run_id = f"eval_{uuid4().hex[:12]}"
        cancel_event = asyncio.Event()
        self._cancel_events[run_id] = cancel_event
        self._client_active[client_id] = run_id
        self._run_clients[run_id] = client_id
        asyncio.create_task(
            self._push_setup_progress(
                client_id,
                run_id,
                "情绪探索任务已入队，正在启动…",
                scenario_id="exploratory",
                tier="exploratory",
            ),
            name=f"eval-ack-{run_id}",
        )
        task = asyncio.create_task(
            self._execute_exploratory(run_id, request, client_id, cancel_event),
            name=f"eval-exploratory-{run_id}",
        )
        self._tasks[run_id] = task
        return run_id

    async def cancel(self, run_id: str) -> bool:
        """Request cancellation for one eval run."""

        cancel_event = self._cancel_events.get(run_id)
        if cancel_event is None:
            return False
        cancel_event.set()
        return True

    async def _execute_scenario(
        self,
        run_id: str,
        scenario_id: str,
        client_id: str,
        cancel_event: asyncio.Event,
    ) -> None:
        recorder: RunRecorder | None = None
        try:
            async with EvalAgentPool.run_guard():
                config = resolve_agent_runtime(load_agent_settings(), load_secrets())
                await self._push_setup_progress(
                    client_id,
                    run_id,
                    "正在加载场景配置…",
                )
                scenario = resolve_scenario_by_id(scenario_id)
                recorder = RunRecorder(
                    run_id=run_id,
                    mode="scenario",
                    tier=scenario.tier,
                    scenario_id=scenario.id,
                    environment=capture_run_environment(config=config),
                )
                await self._push_setup_progress(
                    client_id,
                    run_id,
                    f"场景已就绪：{scenario.description or scenario.id}",
                    scenario_id=scenario.id,
                    tier=scenario.tier,
                    recorder=recorder,
                )

                await self._push_setup_progress(
                    client_id,
                    run_id,
                    "正在获取评测 Agent（首次运行需初始化，可能较慢）…",
                    recorder=recorder,
                )
                agent_client, cold_start = await EvalAgentPool.acquire_client()
                recorder.set_telemetry(agent_cold_start=cold_start, agent_reused=not cold_start)
                await self._push_setup_progress(
                    client_id,
                    run_id,
                    "评测 Agent 已就绪" if not cold_start else "评测 Agent 初始化完成",
                    reused_agent=not cold_start,
                    recorder=recorder,
                )

                judge_runner = None
                if scenario.judge is not None and scenario.judge.enabled:
                    await self._push_setup_progress(
                        client_id,
                        run_id,
                        "正在准备 Judge 模型…",
                        recorder=recorder,
                    )
                    judge_runner = JudgeRunner(build_eval_model(config))
                    await self._push_setup_progress(
                        client_id,
                        run_id,
                        "Judge 模型已就绪",
                        recorder=recorder,
                    )

                async def on_progress(event: EvalProgressEvent) -> None:
                    await self._push_event(client_id, event)

                await EvalRunner(
                    agent_client=agent_client,
                    judge_runner=judge_runner,
                ).run_scenario(
                    scenario,
                    persist=True,
                    progress_callback=on_progress,
                    cancel_event=cancel_event,
                    run_id=run_id,
                    recorder=recorder,
                )
        except Exception as exc:
            _log.exception("eval job failed: run_id=%s", run_id)
            if recorder is not None:
                persist_record_safe(
                    recorder.build(status="failed", error=str(exc)),
                )
            await self._push(
                client_id,
                {
                    "type": "eval_failed",
                    "run_id": run_id,
                    "error": {"code": "eval_run_failed", "message": str(exc)},
                },
            )
        finally:
            self._cleanup_run(run_id, client_id)

    async def _execute_exploratory(
        self,
        run_id: str,
        request: EmotionEvalRequest,
        client_id: str,
        cancel_event: asyncio.Event,
    ) -> None:
        recorder: RunRecorder | None = None
        session: EvalSession | None = None
        try:
            async with EvalAgentPool.run_guard():
                config = resolve_agent_runtime(load_agent_settings(), load_secrets())
                recorder = RunRecorder(
                    run_id=run_id,
                    mode="exploratory",
                    tier="exploratory",
                    scenario_id="exploratory",
                    environment=capture_run_environment(config=config),
                )
                await self._push_setup_progress(
                    client_id,
                    run_id,
                    "正在获取评测 Agent（首次运行需初始化，可能较慢）…",
                    scenario_id="exploratory",
                    tier="exploratory",
                    recorder=recorder,
                )
                from eval.domain.emotion_metrics import EmotionSupportEvaluator
                from eval.domain.simulated_user import SimulatedUser

                agent_client, cold_start = await EvalAgentPool.acquire_client()
                recorder.set_telemetry(agent_cold_start=cold_start, agent_reused=not cold_start)
                await self._push_setup_progress(
                    client_id,
                    run_id,
                    "评测 Agent 已就绪" if not cold_start else "评测 Agent 初始化完成",
                    reused_agent=not cold_start,
                    scenario_id="exploratory",
                    tier="exploratory",
                    recorder=recorder,
                )

                simulated_user = SimulatedUser.from_config(config)
                evaluator = EmotionSupportEvaluator.from_config(config)
                session = EvalSession(
                    simulated_user=simulated_user,
                    agent_client=agent_client,
                    evaluator=evaluator,
                )

                async def on_progress(event: EvalProgressEvent) -> None:
                    await self._push_event(client_id, event)

                response = await session.run(
                    request,
                    run_id=run_id,
                    progress_callback=on_progress,
                    cancel_event=cancel_event,
                    recorder=recorder,
                )
                judge_overall_passed = (
                    response.summary.verdict == "pass" if response.summary is not None else None
                )
                persist_record_safe(
                    build_exploratory_record(
                        recorder,
                        response,
                        observations=session.last_observations,
                        judge_overall_passed=judge_overall_passed,
                    )
                )
        except Exception as exc:
            _log.exception("exploratory eval job failed: run_id=%s", run_id)
            if recorder is not None:
                observations = session.last_observations if session is not None else ()
                persist_record_safe(
                    recorder.build(
                        status="failed",
                        observations=observations,
                        exploratory_config=request,
                        error=str(exc),
                    )
                )
            await self._push(
                client_id,
                {
                    "type": "eval_failed",
                    "run_id": run_id,
                    "error": {"code": "eval_run_failed", "message": str(exc)},
                },
            )
        finally:
            self._cleanup_run(run_id, client_id)

    async def _push_setup_progress(
        self,
        client_id: str,
        run_id: str,
        message: str,
        *,
        recorder: RunRecorder | None = None,
        **extra: object,
    ) -> None:
        payload = {
            "type": "eval_progress",
            "run_id": run_id,
            "phase": "setup",
            "message": message,
            **extra,
        }
        if recorder is not None:
            recorder.record_ws_payload(payload)
        await self._push(client_id, payload)

    async def _push_event(self, client_id: str, event: EvalProgressEvent) -> None:
        payload = {"type": event.type, "run_id": event.run_id, **event.payload}
        await self._push(client_id, payload)

    async def _push(self, client_id: str, payload: dict[str, object]) -> None:
        sent = await self._notifier.send_to_client(client_id, payload)
        if not sent:
            _log.debug("eval progress not delivered; client offline: %s", client_id)

    def _cleanup_run(self, run_id: str, client_id: str) -> None:
        self._tasks.pop(run_id, None)
        self._cancel_events.pop(run_id, None)
        self._run_clients.pop(run_id, None)
        if self._client_active.get(client_id) == run_id:
            self._client_active.pop(client_id, None)
