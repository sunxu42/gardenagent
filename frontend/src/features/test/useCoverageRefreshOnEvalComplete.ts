import { useEffect, useRef } from "react";

import { useEvalRun } from "@/features/test/EvalRunProvider";
import type { EvalRunRootState } from "@/features/test/evalBatchTypes";

export function shouldRefreshCoverageMatrix(state: EvalRunRootState): boolean {
  return state.items.some(
    (item) =>
      item.scenarioId !== "exploratory" &&
      item.live.tier !== "exploratory" &&
      (item.status === "completed" || item.status === "failed"),
  );
}

export function useCoverageRefreshOnEvalComplete(
  reload: (options?: { silent?: boolean }) => Promise<void>,
): void {
  const { state } = useEvalRun();
  const prevBatchStatusRef = useRef(state.batchStatus);

  useEffect(() => {
    const previousStatus = prevBatchStatusRef.current;
    prevBatchStatusRef.current = state.batchStatus;

    if (previousStatus !== "running" || state.batchStatus !== "completed") {
      return;
    }
    if (!shouldRefreshCoverageMatrix(state)) {
      return;
    }
    void reload({ silent: true });
  }, [reload, state]);
}
