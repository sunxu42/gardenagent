import type { EvalRunResponse } from "@/features/test/types";
import type { EvalProgressSnapshot, EvalRunPhase } from "@/features/test/evalProgress";

export interface LiveEvalRunState {
  activeRunId: string | null;
  scenarioId: string | null;
  tier: string | null;
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
  progressMessage: string | null;
  phase: EvalRunPhase;
  agentProgress: { current: number; total: number } | null;
  judgeProgress: { current: number; total: number } | null;
  timeline: EvalProgressSnapshot["timeline"];
  liveResult: Partial<EvalRunResponse>;
  error: string | null;
}

export type BatchItemStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface BatchEvalItem {
  scenarioId: string;
  runId: string | null;
  status: BatchItemStatus;
  expanded: boolean;
  live: LiveEvalRunState;
}

export interface EvalRunRootState {
  batchId: string | null;
  items: BatchEvalItem[];
  focusedScenarioId: string | null;
  batchStatus: "idle" | "running" | "completed";
}

export function isTerminalBatchItemStatus(status: BatchItemStatus): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}

export function getFocusedItem(state: EvalRunRootState): BatchEvalItem | null {
  if (state.items.length === 0) {
    return null;
  }
  if (state.focusedScenarioId) {
    const focused = state.items.find((item) => item.scenarioId === state.focusedScenarioId);
    if (focused) {
      return focused;
    }
  }
  const running = state.items.find((item) => item.status === "running");
  if (running) {
    return running;
  }
  return state.items[state.items.length - 1] ?? null;
}

export function getRunningItem(state: EvalRunRootState): BatchEvalItem | null {
  return state.items.find((item) => item.status === "running") ?? null;
}

export function getNextPendingItem(state: EvalRunRootState): BatchEvalItem | null {
  return state.items.find((item) => item.status === "pending") ?? null;
}

export function shouldShowBatchQueue(state: EvalRunRootState): boolean {
  return state.items.length > 1;
}

export function countFinishedItems(state: EvalRunRootState): number {
  return state.items.filter((item) => isTerminalBatchItemStatus(item.status)).length;
}
