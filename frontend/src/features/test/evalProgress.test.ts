import { applyEvalWsProgress, createInitialEvalProgress } from "@/features/test/evalProgress";

describe("applyEvalWsProgress", () => {
  it("records eval_progress messages in timeline", () => {
    const next = applyEvalWsProgress(createInitialEvalProgress(), {
      type: "eval_progress",
      run_id: "run-1",
      phase: "agent",
      message: "第 1/2 轮：Agent 回复中…",
      round: 1,
      total_rounds: 2,
    });
    expect(next.message).toContain("Agent 回复中");
    expect(next.agentProgress).toEqual({ current: 1, total: 2 });
    expect(next.timeline).toHaveLength(1);
  });

  it("records eval_turn with assistant fallback", () => {
    const next = applyEvalWsProgress(createInitialEvalProgress(), {
      type: "eval_turn",
      run_id: "run-1",
      round: 1,
      user: "你好",
      assistant: "你好呀",
    });
    expect(next.timeline[0]?.title).toBe("第 1 轮完成");
  });
});
