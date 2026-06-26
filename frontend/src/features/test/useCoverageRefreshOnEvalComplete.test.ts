import { describe, expect, it } from "vitest";

import { initialEvalRunRootState } from "@/features/test/evalRunStore";
import { shouldRefreshCoverageMatrix } from "@/features/test/useCoverageRefreshOnEvalComplete";

describe("shouldRefreshCoverageMatrix", () => {
  it("returns true when a scenario batch item completed", () => {
    const state = {
      ...initialEvalRunRootState,
      batchStatus: "completed" as const,
      items: [
        {
          scenarioId: "smoke/greeting_01",
          runId: "run-1",
          status: "completed" as const,
          expanded: false,
          live: {
            activeRunId: "run-1",
            scenarioId: "smoke/greeting_01",
            tier: "smoke",
            status: "completed" as const,
            progressMessage: null,
            phase: "completed" as const,
            agentProgress: null,
            judgeProgress: null,
            timeline: [],
            liveResult: {},
            error: null,
          },
        },
      ],
    };

    expect(shouldRefreshCoverageMatrix(state)).toBe(true);
  });

  it("returns false for exploratory-only batches", () => {
    const state = {
      ...initialEvalRunRootState,
      batchStatus: "completed" as const,
      items: [
        {
          scenarioId: "exploratory",
          runId: "run-2",
          status: "completed" as const,
          expanded: false,
          live: {
            activeRunId: "run-2",
            scenarioId: "exploratory",
            tier: "exploratory",
            status: "completed" as const,
            progressMessage: null,
            phase: "completed" as const,
            agentProgress: null,
            judgeProgress: null,
            timeline: [],
            liveResult: {},
            error: null,
          },
        },
      ],
    };

    expect(shouldRefreshCoverageMatrix(state)).toBe(false);
  });
});
