from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from langchain_core.tools import StructuredTool
from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

from yard.events import InputEvent, USER_INPUT_EVENT

DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_WAKE_MODE = "next-heartbeat"
RUN_HISTORY_LIMIT = 50


def _to_datetime(value: Any, default_tz: str = DEFAULT_TIMEZONE) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1000.0, tz=ZoneInfo(default_tz))
    if not isinstance(value, str):
        raise ValueError("schedule.at must be ISO string or epoch milliseconds")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo(default_tz))
    return parsed


class LocalSchedulerService:
    def __init__(self, agent: Any, timezone_name: str = DEFAULT_TIMEZONE):
        self.agent = agent
        self.timezone_name = timezone_name
        self.timezone = ZoneInfo(timezone_name)
        self.scheduler = AsyncIOScheduler(
            timezone=self.timezone,
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 30,
            },
        )
        self._metadata: dict[str, dict[str, Any]] = {}
        self._runs: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=RUN_HISTORY_LIMIT))
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.start()
        self._started = True
        _log.info(f"local scheduler started, timezone={self.timezone_name}")

    async def shutdown(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False
        _log.info("local scheduler stopped")

    async def request_wake(self, text: str, mode: str = DEFAULT_WAKE_MODE) -> dict[str, Any]:
        if mode == "now":
            await self._enqueue_event(text)
            return {"ok": True, "mode": mode, "message": "wake event enqueued immediately"}
        self.agent._cron_wake_pending_text = text
        return {"ok": True, "mode": "next-heartbeat", "message": "wake queued for next heartbeat slot"}

    async def consume_pending_wake(self) -> bool:
        text = getattr(self.agent, "_cron_wake_pending_text", None)
        if not text:
            return False
        self.agent._cron_wake_pending_text = None
        await self._enqueue_event(text)
        return True

    def status(self) -> dict[str, Any]:
        jobs = self.scheduler.get_jobs()
        return {
            "ok": True,
            "running": self._started,
            "timezone": self.timezone_name,
            "jobsCount": len(jobs),
        }

    def list_jobs(self, include_disabled: bool = False) -> dict[str, Any]:
        items = []
        for job in self.scheduler.get_jobs():
            metadata = self._metadata.get(job.id, {})
            enabled = metadata.get("enabled", True)
            if not enabled and not include_disabled:
                continue
            items.append(
                {
                    "jobId": job.id,
                    "name": metadata.get("name"),
                    "enabled": enabled,
                    "schedule": metadata.get("schedule"),
                    "payload": metadata.get("payload"),
                    "nextRunAt": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )
        return {"ok": True, "jobs": items}

    def add_job(self, job_spec: dict[str, Any]) -> dict[str, Any]:
        schedule = job_spec.get("schedule") or {}
        payload = job_spec.get("payload") or {}
        if not schedule or not payload:
            raise ValueError("job.schedule and job.payload are required")
        self._validate_schedule_for_add(schedule)
        trigger = self._build_trigger(schedule)
        job_id = job_spec.get("jobId") or uuid.uuid4().hex
        enabled = bool(job_spec.get("enabled", True))
        aps_job = self.scheduler.add_job(
            self._scheduled_execute,
            trigger=trigger,
            id=job_id,
            kwargs={"job_id": job_id},
            replace_existing=False,
        )
        if not enabled:
            self.scheduler.pause_job(job_id)
        self._metadata[job_id] = {
            "name": job_spec.get("name"),
            "schedule": schedule,
            "payload": payload,
            "enabled": enabled,
        }
        return {
            "ok": True,
            "jobId": job_id,
            "nextRunAt": aps_job.next_run_time.isoformat() if aps_job.next_run_time else None,
        }

    def _validate_schedule_for_add(self, schedule: dict[str, Any]) -> None:
        kind = schedule.get("kind")
        if kind != "at":
            return
        run_at = _to_datetime(schedule.get("at"), self.timezone_name)
        now = datetime.now(self.timezone)
        # Reject obviously expired one-shot jobs so LLM gets immediate feedback.
        if run_at <= now:
            raise ValueError(
                f"schedule.at is in the past: {run_at.isoformat()} <= now {now.isoformat()}; "
                "please provide a future time"
            )

    def update_job(self, job_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        if job_id not in self._metadata:
            raise ValueError(f"job not found: {job_id}")
        meta = self._metadata[job_id]
        if "name" in patch:
            meta["name"] = patch["name"]
        if "payload" in patch:
            meta["payload"] = patch["payload"]
        if "schedule" in patch:
            trigger = self._build_trigger(patch["schedule"])
            self.scheduler.reschedule_job(job_id, trigger=trigger)
            meta["schedule"] = patch["schedule"]
        if "enabled" in patch:
            enabled = bool(patch["enabled"])
            meta["enabled"] = enabled
            if enabled:
                self.scheduler.resume_job(job_id)
            else:
                self.scheduler.pause_job(job_id)
        job = self.scheduler.get_job(job_id)
        return {
            "ok": True,
            "jobId": job_id,
            "nextRunAt": job.next_run_time.isoformat() if job and job.next_run_time else None,
        }

    def remove_job(self, job_id: str) -> dict[str, Any]:
        self.scheduler.remove_job(job_id)
        self._metadata.pop(job_id, None)
        return {"ok": True, "jobId": job_id}

    async def run_job_now(self, job_id: str) -> dict[str, Any]:
        await self._execute_job(job_id)
        return {"ok": True, "jobId": job_id, "runMode": "force"}

    def get_runs(self, job_id: str) -> dict[str, Any]:
        return {"ok": True, "jobId": job_id, "runs": list(self._runs.get(job_id, []))}

    async def _scheduled_execute(self, job_id: str) -> None:
        await self._execute_job(job_id)

    async def _execute_job(self, job_id: str) -> None:
        started_at = datetime.now(timezone.utc)
        meta = self._metadata.get(job_id)
        if not meta:
            return
        payload = meta.get("payload") or {}
        try:
            text = self._payload_to_text(payload)
            await self._enqueue_event(text)
            ended_at = datetime.now(timezone.utc)
            self._runs[job_id].append(
                {
                    "status": "ok",
                    "startedAt": started_at.isoformat(),
                    "endedAt": ended_at.isoformat(),
                    "latencyMs": int((ended_at - started_at).total_seconds() * 1000),
                }
            )
        except Exception as e:
            ended_at = datetime.now(timezone.utc)
            self._runs[job_id].append(
                {
                    "status": "error",
                    "startedAt": started_at.isoformat(),
                    "endedAt": ended_at.isoformat(),
                    "error": str(e),
                }
            )
            _log.error(f"scheduled job failed, job_id={job_id}, error={e}")

    async def _enqueue_event(self, text: str) -> None:
        event = InputEvent(content=text, event_id=uuid.uuid4().hex, event_type=USER_INPUT_EVENT)
        await self.agent.agent_input_queue.put(event)

    def _build_trigger(self, schedule: dict[str, Any]):
        kind = schedule.get("kind")
        if kind == "at":
            return DateTrigger(run_date=_to_datetime(schedule.get("at"), self.timezone_name), timezone=self.timezone)
        if kind == "every":
            every_ms = schedule.get("everyMs")
            if every_ms is None:
                raise ValueError("schedule.everyMs is required for kind='every'")
            anchor = schedule.get("anchorMs")
            start_date = _to_datetime(anchor, self.timezone_name) if anchor is not None else None
            return IntervalTrigger(seconds=float(every_ms) / 1000.0, start_date=start_date, timezone=self.timezone)
        if kind == "cron":
            expr = schedule.get("expr")
            if not expr:
                raise ValueError("schedule.expr is required for kind='cron'")
            tz_name = schedule.get("tz") or self.timezone_name
            return CronTrigger.from_crontab(expr, timezone=ZoneInfo(tz_name))
        raise ValueError(f"unsupported schedule kind: {kind}")

    @staticmethod
    def _payload_to_text(payload: dict[str, Any]) -> str:
        kind = payload.get("kind")
        if kind == "systemEvent":
            text = payload.get("text")
            if not text:
                raise ValueError("payload.text is required for kind='systemEvent'")
            return text
        if kind == "agentTurn":
            message = payload.get("message")
            if not message:
                raise ValueError("payload.message is required for kind='agentTurn'")
            return message
        raise ValueError(f"unsupported payload kind: {kind}")


def create_cron_tool(service: LocalSchedulerService) -> StructuredTool:
    async def cron(
        action: str,
        includeDisabled: bool = False,
        job: dict[str, Any] | None = None,
        jobId: str | None = None,
        id: str | None = None,
        patch: dict[str, Any] | None = None,
        text: str | None = None,
        mode: str = DEFAULT_WAKE_MODE,
        runMode: str = "force",
        contextMessages: int = 0,
        gatewayUrl: str | None = None,
        gatewayToken: str | None = None,
        timeoutMs: int | None = None,
    ) -> dict[str, Any]:
        del contextMessages, gatewayUrl, gatewayToken, timeoutMs, runMode
        canonical_id = jobId or id

        try:
            if action == "status":
                return service.status()
            if action == "list":
                return service.list_jobs(include_disabled=includeDisabled)
            if action == "add":
                return service.add_job(job or {})
            if action == "update":
                if not canonical_id:
                    raise ValueError("jobId is required for update")
                return service.update_job(canonical_id, patch or {})
            if action == "remove":
                if not canonical_id:
                    raise ValueError("jobId is required for remove")
                return service.remove_job(canonical_id)
            if action == "run":
                if not canonical_id:
                    raise ValueError("jobId is required for run")
                return await service.run_job_now(canonical_id)
            if action == "runs":
                if not canonical_id:
                    raise ValueError("jobId is required for runs")
                return service.get_runs(canonical_id)
            if action == "wake":
                if not text:
                    raise ValueError("text is required for wake")
                return await service.request_wake(text=text, mode=mode)
            raise ValueError(f"unsupported action: {action}")
        except Exception as e:
            _log.error(f"cron action failed, action={action}, error={e}")
            return {"ok": False, "action": action, "error": str(e)}

    return StructuredTool.from_function(
        name="cron",
        description="""Manage local APScheduler jobs and wake events (runs inside this same Python process).

ACTIONS:
- status: Check scheduler running status and timezone.
- list: List jobs (use includeDisabled:true to include paused jobs).
- add: Create a job (requires job object).
- update: Modify a job (requires jobId + patch object).
- remove: Delete a job (requires jobId).
- run: Trigger a job immediately (requires jobId).
- runs: Get in-memory run history (recent items) for a job (requires jobId).
- wake: Send a wake event (requires text, optional mode).

JOB SCHEMA (for add action, JSON object):
{
  "name": "string (optional)",
  "schedule": { ... },      // Required
  "payload": { ... },       // Required
  "enabled": true | false   // Optional, default true
}

SCHEDULE TYPES (schedule.kind):
- "at": One-shot absolute time
  { "kind": "at", "at": "<ISO-8601 timestamp or epoch-ms>" }
- "every": Recurring interval
  { "kind": "every", "everyMs": <interval-ms>, "anchorMs": <optional-start-epoch-ms> }
- "cron": Cron expression
  { "kind": "cron", "expr": "<cron-expression>", "tz": "<optional-timezone>" }

TIMEZONE RULES:
- Default timezone is Asia/Shanghai (Beijing time).
- For schedule.kind="cron", if schedule.tz is omitted, Asia/Shanghai is used.
- For schedule.at values:
  - ISO timestamps with explicit offset (Z / +08:00 / etc.) are respected.
  - ISO timestamps without timezone offset are treated as Asia/Shanghai.

PAYLOAD TYPES (payload.kind) - what gets enqueued to the agent input queue:
- "systemEvent": enqueue payload.text
  { "kind": "systemEvent", "text": "<message>" }
- "agentTurn": enqueue payload.message
  { "kind": "agentTurn", "message": "<prompt>" }

WAKE MODES (for wake action):
- "next-heartbeat" (default): queued wake is consumed on next heartbeat tick.
- "now": enqueue immediately.

COMPATIBILITY NOTES:
- jobId is the canonical identifier; id is accepted for compatibility.
- gatewayUrl/gatewayToken/timeoutMs/runMode/contextMessages are accepted but ignored in local mode.
- delivery/sessionTarget are not implemented in local mode; ignore them and only use payload.kind/text/message.
- run history is in-memory only (recent items per job).""",
        coroutine=cron,
    )