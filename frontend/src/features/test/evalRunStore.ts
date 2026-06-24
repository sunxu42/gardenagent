import type {
  EmotionTurnResult,
  EvalRunResponse,
} from "@/features/test/types";
import type { EvalWsEvent } from "@/features/test/evalWsTypes";
import { applyEvalWsProgress } from "@/features/test/evalProgress";
import type {
  BatchEvalItem,
  BatchItemStatus,
  EvalRunRootState,
  LiveEvalRunState,
} from "@/features/test/evalBatchTypes";

export type { LiveEvalRunState, EvalRunRootState, BatchEvalItem } from "@/features/test/evalBatchTypes";

export const initialLiveEvalRunState: LiveEvalRunState = {
  activeRunId: null,
  scenarioId: null,
  tier: null,
  status: "idle",
  progressMessage: null,
  phase: "idle",
  agentProgress: null,
  judgeProgress: null,
  timeline: [],
  liveResult: {},
  error: null,
};

export const initialEvalRunRootState: EvalRunRootState = {
  batchId: null,
  items: [],
  focusedScenarioId: null,
  batchStatus: "idle",
};

export type EvalRunAction =
  | { type: "BATCH_STARTED"; payload: { scenarioIds: string[]; batchId?: string } }
  | { type: "BATCH_ADVANCE" }
  | { type: "RUN_STARTED"; payload: { runId: string; scenarioId: string; tier: string } }
  | { type: "WS_EVENT"; payload: EvalWsEvent }
  | { type: "BATCH_FOCUS"; payload: { scenarioId: string } }
  | { type: "BATCH_TOGGLE_EXPAND"; payload: { scenarioId: string } }
  | { type: "BATCH_CANCEL" }
  | { type: "LOAD_RESULT"; payload: EvalRunResponse }
  | { type: "RESET" };

function upsertTurn(
  observations: EmotionTurnResult[],
  turn: EmotionTurnResult,
): EmotionTurnResult[] {
  const others = observations.filter((item) => item.round !== turn.round);
  return [...others, turn].sort((a, b) => a.round - b.round);
}

function mergeProgress(
  state: LiveEvalRunState,
  event: EvalWsEvent,
): Pick<
  LiveEvalRunState,
  "progressMessage" | "phase" | "agentProgress" | "judgeProgress" | "timeline"
> {
  const progress = applyEvalWsProgress(
    {
      phase: state.phase,
      message: state.progressMessage,
      agentProgress: state.agentProgress,
      judgeProgress: state.judgeProgress,
      timeline: state.timeline,
    },
    event,
  );
  return {
    progressMessage: progress.message,
    phase: progress.phase,
    agentProgress: progress.agentProgress,
    judgeProgress: progress.judgeProgress,
    timeline: progress.timeline,
  };
}

function createPreRunLive(scenarioId: string): LiveEvalRunState {
  return {
    ...initialLiveEvalRunState,
    scenarioId,
    status: "running",
    progressMessage: "准备启动…",
    phase: "starting",
    liveResult: {
      scenario_id: scenarioId,
      status: "running",
      observations: [],
      assertions: [],
      judge: [],
    },
  };
}

function createPendingLive(scenarioId: string): LiveEvalRunState {
  return {
    ...initialLiveEvalRunState,
    scenarioId,
    status: "idle",
    liveResult: { scenario_id: scenarioId },
  };
}

function createRunStartedLive(
  runId: string,
  scenarioId: string,
  tier: string,
): LiveEvalRunState {
  return {
    activeRunId: runId,
    scenarioId,
    tier,
    status: "running",
    progressMessage: "评测任务已入队…",
    phase: "starting",
    agentProgress: null,
    judgeProgress: null,
    timeline: [
      {
        id: "tl-start",
        at: Date.now(),
        tone: "info",
        title: "已提交评测任务",
        detail: scenarioId,
      },
    ],
        liveResult: {
          run_id: runId,
          scenario_id: scenarioId,
          tier: tier as EvalRunResponse["tier"],
          mode: tier === "exploratory" ? "exploratory" : "scenario",
          status: "running",
      observations: [],
      assertions: [],
      judge: [],
    },
    error: null,
  };
}

function liveStatusToBatchStatus(
  status: LiveEvalRunState["status"],
): BatchItemStatus | null {
  if (status === "running") {
    return "running";
  }
  if (status === "completed") {
    return "completed";
  }
  if (status === "failed") {
    return "failed";
  }
  if (status === "cancelled") {
    return "cancelled";
  }
  return null;
}

function loadResultToLive(payload: EvalRunResponse): LiveEvalRunState {
  const status =
    payload.status === "cancelled"
      ? "cancelled"
      : payload.status === "failed"
        ? "failed"
        : payload.status === "running"
          ? "running"
          : "completed";
  return {
    activeRunId: payload.run_id,
    scenarioId: payload.scenario_id ?? null,
    tier: payload.tier,
    status,
    progressMessage: null,
    phase:
      payload.status === "cancelled"
        ? "cancelled"
        : payload.status === "failed"
          ? "failed"
          : "completed",
    agentProgress: null,
    judgeProgress: null,
    timeline: [],
    liveResult: payload,
    error: payload.error?.message ?? null,
  };
}

function applyWsEventToLive(
  state: LiveEvalRunState,
  event: EvalWsEvent,
): LiveEvalRunState {
  if (state.activeRunId && event.run_id !== state.activeRunId) {
    return state;
  }
  const liveResult = { ...state.liveResult };
  const progressPatch = mergeProgress(state, event);

  if (event.type === "eval_started") {
    return {
      ...state,
      ...progressPatch,
      activeRunId: event.run_id,
      scenarioId: event.scenario_id ?? state.scenarioId,
      tier: event.tier ?? state.tier,
      status: "running",
      liveResult: {
        ...liveResult,
        run_id: event.run_id,
        scenario_id: event.scenario_id ?? liveResult.scenario_id,
        tier: (event.tier as EvalRunResponse["tier"]) ?? liveResult.tier,
        mode: event.tier === "exploratory" ? "exploratory" : liveResult.mode ?? "scenario",
        status: "running",
      },
    };
  }
  if (event.type === "eval_turn" && event.round != null && event.user != null) {
    const observations = upsertTurn(liveResult.observations ?? [], {
      round: event.round,
      user: event.user,
      assistant: event.assistant ?? "",
      agent_affect: event.agent_affect,
    });
    return {
      ...state,
      ...progressPatch,
      liveResult: { ...liveResult, observations },
    };
  }
  if (event.type === "eval_assertions" && event.assertions) {
    return {
      ...state,
      ...progressPatch,
      liveResult: { ...liveResult, assertions: event.assertions },
    };
  }
  if (event.type === "eval_judge_metric" && event.name) {
    const judge = [...(liveResult.judge ?? [])];
    const next = {
      name: event.name,
      score: event.score ?? 0,
      passed: Boolean(event.passed),
      threshold: event.threshold ?? 0,
      reason: event.reason ?? "",
    };
    const index = judge.findIndex((item) => item.name === next.name);
    if (index >= 0) {
      judge[index] = next;
    } else {
      judge.push(next);
    }
    return {
      ...state,
      ...progressPatch,
      liveResult: { ...liveResult, judge },
    };
  }
  if (event.type === "eval_completed") {
    return {
      ...state,
      ...progressPatch,
      status: event.status === "failed" ? "failed" : "completed",
      liveResult: {
        ...liveResult,
        status: event.status === "failed" ? "failed" : "completed",
        judge_overall_passed: event.judge_overall_passed,
        scores: event.scores ?? liveResult.scores,
        summary: event.summary ?? liveResult.summary,
        tier: (event.tier as EvalRunResponse["tier"]) ?? liveResult.tier ?? state.tier,
        mode: liveResult.mode ?? "exploratory",
      },
    };
  }
  if (event.type === "eval_failed") {
    return {
      ...state,
      ...progressPatch,
      status: "failed",
      error: event.error?.message ?? "评测失败",
      liveResult: { ...liveResult, status: "failed" },
    };
  }
  if (event.type === "eval_cancelled") {
    return {
      ...state,
      ...progressPatch,
      status: "cancelled",
      liveResult: { ...liveResult, status: "cancelled" },
    };
  }
  if (event.type === "eval_progress") {
    return {
      ...state,
      ...progressPatch,
    };
  }
  return state;
}

function findItemIndexForWsEvent(
  items: BatchEvalItem[],
  event: EvalWsEvent,
): number {
  const byRunId = items.findIndex((item) => item.runId === event.run_id);
  if (byRunId >= 0) {
    return byRunId;
  }
  if (event.type === "eval_started") {
    return items.findIndex((item) => item.status === "running" && item.runId == null);
  }
  return -1;
}

function syncBatchCompletion(state: EvalRunRootState): EvalRunRootState["batchStatus"] {
  if (state.batchStatus !== "running") {
    return state.batchStatus;
  }
  const hasActive = state.items.some(
    (item) => item.status === "running" || item.status === "pending",
  );
  return hasActive ? "running" : "completed";
}

function mapItems(
  items: BatchEvalItem[],
  scenarioId: string,
  updater: (item: BatchEvalItem) => BatchEvalItem,
): BatchEvalItem[] {
  return items.map((item) => (item.scenarioId === scenarioId ? updater(item) : item));
}

export function evalRunReducer(
  state: EvalRunRootState,
  action: EvalRunAction,
): EvalRunRootState {
  switch (action.type) {
    case "BATCH_STARTED": {
      const { scenarioIds } = action.payload;
      if (scenarioIds.length === 0) {
        return state;
      }
      const batchId = action.payload.batchId ?? `batch-${Date.now()}`;
      const items: BatchEvalItem[] = scenarioIds.map((scenarioId, index) => ({
        scenarioId,
        runId: null,
        status: index === 0 ? "running" : "pending",
        expanded: false,
        live: index === 0 ? createPreRunLive(scenarioId) : createPendingLive(scenarioId),
      }));
      return {
        batchId,
        items,
        focusedScenarioId: scenarioIds[0],
        batchStatus: "running",
      };
    }
    case "BATCH_ADVANCE": {
      if (state.items.some((item) => item.status === "running")) {
        return state;
      }
      const nextIndex = state.items.findIndex((item) => item.status === "pending");
      if (nextIndex < 0) {
        return { ...state, batchStatus: "completed" };
      }
      const items = state.items.map((item, index) =>
        index === nextIndex
          ? {
              ...item,
              status: "running" as const,
              live: createPreRunLive(item.scenarioId),
            }
          : item,
      );
      return {
        ...state,
        items,
        focusedScenarioId: items[nextIndex].scenarioId,
        batchStatus: "running",
      };
    }
    case "RUN_STARTED": {
      const { runId, scenarioId, tier } = action.payload;
      const items = mapItems(state.items, scenarioId, (item) => ({
        ...item,
        runId,
        status: "running",
        live: createRunStartedLive(runId, scenarioId, tier),
      }));
      const next: EvalRunRootState = {
        ...state,
        items,
        focusedScenarioId: state.focusedScenarioId ?? scenarioId,
        batchStatus: state.batchStatus === "idle" ? "running" : state.batchStatus,
      };
      if (next.items.length === 1 && !next.batchId) {
        next.batchId = `batch-${Date.now()}`;
      }
      return next;
    }
    case "WS_EVENT": {
      const event = action.payload;
      const itemIndex = findItemIndexForWsEvent(state.items, event);
      if (itemIndex < 0) {
        return state;
      }
      const items = [...state.items];
      const current = items[itemIndex];
      const nextLive = applyWsEventToLive(current.live, event);
      const nextBatchStatus = liveStatusToBatchStatus(nextLive.status);
      items[itemIndex] = {
        ...current,
        runId: nextLive.activeRunId ?? current.runId ?? event.run_id,
        status: nextBatchStatus ?? current.status,
        live: nextLive,
      };
      const nextState: EvalRunRootState = {
        ...state,
        items,
        focusedScenarioId:
          current.status === "running" ? current.scenarioId : state.focusedScenarioId,
      };
      nextState.batchStatus = syncBatchCompletion(nextState);
      return nextState;
    }
    case "BATCH_FOCUS":
      return {
        ...state,
        focusedScenarioId: action.payload.scenarioId,
      };
    case "BATCH_TOGGLE_EXPAND":
      return {
        ...state,
        items: mapItems(state.items, action.payload.scenarioId, (item) => ({
          ...item,
          expanded: !item.expanded,
        })),
      };
    case "BATCH_CANCEL": {
      const items = state.items.map((item) => {
        if (item.status === "pending" || item.status === "running") {
          return {
            ...item,
            status: "cancelled" as const,
            live: {
              ...item.live,
              status: "cancelled" as const,
              liveResult: { ...item.live.liveResult, status: "cancelled" as const },
            },
          };
        }
        return item;
      });
      return {
        ...state,
        items,
        batchStatus: "completed",
      };
    }
    case "LOAD_RESULT": {
      const payload = action.payload;
      const scenarioId = payload.scenario_id ?? "";
      const itemStatus: BatchItemStatus =
        payload.status === "cancelled"
          ? "cancelled"
          : payload.status === "failed"
            ? "failed"
            : payload.status === "running"
              ? "running"
              : "completed";
      return {
        batchId: null,
        batchStatus: "idle",
        focusedScenarioId: scenarioId || null,
        items: scenarioId
          ? [
              {
                scenarioId,
                runId: payload.run_id,
                status: itemStatus,
                expanded: true,
                live: loadResultToLive(payload),
              },
            ]
          : [],
      };
    }
    case "RESET":
      return initialEvalRunRootState;
    default:
      return state;
  }
}
