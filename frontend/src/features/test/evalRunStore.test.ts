import { describe, expect, it } from "vitest";

import {
  evalRunReducer,
  initialEvalRunRootState,
} from "@/features/test/evalRunStore";

describe("evalRunReducer batch", () => {
  it("initializes a batch from BATCH_STARTED", () => {
    const next = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["a", "b", "c"] },
    });
    expect(next.batchStatus).toBe("running");
    expect(next.items).toHaveLength(3);
    expect(next.items[0]?.status).toBe("running");
    expect(next.items[1]?.status).toBe("pending");
    expect(next.focusedScenarioId).toBe("a");
  });

  it("applies RUN_STARTED to the active scenario item", () => {
    const batch = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["greeting_01"] },
    });
    const next = evalRunReducer(batch, {
      type: "RUN_STARTED",
      payload: { runId: "run-1", scenarioId: "greeting_01", tier: "smoke" },
    });
    expect(next.items[0]?.runId).toBe("run-1");
    expect(next.items[0]?.live.activeRunId).toBe("run-1");
    expect(next.items[0]?.live.status).toBe("running");
  });

  it("routes WS events by run_id without clearing other items", () => {
    const batch = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["a", "b"] },
    });
    const started = evalRunReducer(batch, {
      type: "RUN_STARTED",
      payload: { runId: "run-1", scenarioId: "a", tier: "smoke" },
    });
    const afterTurn = evalRunReducer(started, {
      type: "WS_EVENT",
      payload: {
        type: "eval_turn",
        run_id: "run-1",
        round: 1,
        user: "你好",
        assistant: "你好呀",
      },
    });
    const completed = evalRunReducer(afterTurn, {
      type: "WS_EVENT",
      payload: {
        type: "eval_completed",
        run_id: "run-1",
        status: "completed",
        judge_overall_passed: true,
      },
    });

    expect(completed.items[0]?.status).toBe("completed");
    expect(completed.items[0]?.live.liveResult.observations).toHaveLength(1);
    expect(completed.items[1]?.status).toBe("pending");
    expect(completed.items[1]?.live.timeline).toHaveLength(0);
  });

  it("advances pending items with BATCH_ADVANCE", () => {
    let batch = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["a", "b"] },
    });
    batch = evalRunReducer(batch, {
      type: "RUN_STARTED",
      payload: { runId: "run-1", scenarioId: "a", tier: "smoke" },
    });
    batch = evalRunReducer(batch, {
      type: "WS_EVENT",
      payload: {
        type: "eval_completed",
        run_id: "run-1",
        status: "completed",
        judge_overall_passed: true,
      },
    });
    const advanced = evalRunReducer(batch, {
      type: "BATCH_ADVANCE",
    });
    expect(advanced.items[0]?.status).toBe("completed");
    expect(advanced.items[1]?.status).toBe("running");
    expect(advanced.focusedScenarioId).toBe("b");
  });

  it("ignores WS events for unknown runs", () => {
    const batch = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["greeting_01"] },
    });
    const running = evalRunReducer(batch, {
      type: "RUN_STARTED",
      payload: { runId: "run-1", scenarioId: "greeting_01", tier: "smoke" },
    });
    const next = evalRunReducer(running, {
      type: "WS_EVENT",
      payload: {
        type: "eval_progress",
        run_id: "run-other",
        message: "ignored",
      },
    });
    expect(next.items[0]?.live.progressMessage).toBe("评测任务已入队…");
  });

  it("stores exploratory summary from eval_completed event", () => {
    let batch = evalRunReducer(initialEvalRunRootState, {
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["exploratory"] },
    });
    batch = evalRunReducer(batch, {
      type: "RUN_STARTED",
      payload: { runId: "run-exp", scenarioId: "exploratory", tier: "exploratory" },
    });
    const completed = evalRunReducer(batch, {
      type: "WS_EVENT",
      payload: {
        type: "eval_completed",
        run_id: "run-exp",
        status: "completed",
        judge_overall_passed: true,
        scores: [{ name: "empathy", score: 0.8, reason: "ok", evidence: [] }],
        summary: {
          overall_score: 0.8,
          verdict: "pass",
          conclusion: "情绪支持稳定。",
          improvement_suggestions: [],
        },
      },
    });
    expect(completed.items[0]?.live.liveResult.summary?.conclusion).toBe("情绪支持稳定。");
    expect(completed.items[0]?.live.liveResult.scores).toHaveLength(1);
  });
});
