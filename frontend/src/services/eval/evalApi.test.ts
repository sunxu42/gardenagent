import { afterEach, describe, expect, it, vi } from "vitest";
import { runEmotionEval } from "./evalApi";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("runEmotionEval", () => {
  it("posts scenario and returns typed result", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          session_id: "eval_test",
          status: "completed",
          turns: [],
          scores: [],
          summary: {
            overall_score: 0.8,
            verdict: "pass",
            conclusion: "ok",
            improvement_suggestions: [],
          },
        }),
      }),
    );

    const result = await runEmotionEval({
      background: "工作压力大",
      initial_mood: "anxious",
      rounds: 1,
      goal: "评估 agent 的情绪支持质量",
    });

    expect(fetch).toHaveBeenCalledWith(
      "/api/eval/emotion-support/run",
      expect.objectContaining({ method: "POST" }),
    );
    expect(result.status).toBe("completed");
  });

  it("throws payload error when evaluation status is failed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "failed",
          error: { code: "invalid_request", message: "bad request" },
        }),
      }),
    );

    await expect(
      runEmotionEval({
        background: "工作压力大",
        initial_mood: "anxious",
        rounds: 1,
        goal: "评估 agent 的情绪支持质量",
      }),
    ).rejects.toThrow("bad request");
  });

  it("throws fallback error on HTTP error without payload message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          session_id: "eval_test",
          status: "completed",
          turns: [],
          scores: [],
          summary: null,
        }),
      }),
    );

    await expect(
      runEmotionEval({
        background: "工作压力大",
        initial_mood: "anxious",
        rounds: 1,
        goal: "评估 agent 的情绪支持质量",
      }),
    ).rejects.toThrow("评测运行失败");
  });

  it("throws readable error when failed response is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => {
          throw new SyntaxError("Unexpected token < in JSON");
        },
      }),
    );

    await expect(
      runEmotionEval({
        background: "工作压力大",
        initial_mood: "anxious",
        rounds: 1,
        goal: "评估 agent 的情绪支持质量",
      }),
    ).rejects.toThrow("评测运行失败");
  });
});
