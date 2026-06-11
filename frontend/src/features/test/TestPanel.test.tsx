import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { EmotionEvalRequest } from "@/features/test/types";
import { runEmotionEval } from "@/services/eval/evalApi";

import { TestPanel } from "./TestPanel";

vi.mock("@/services/eval/evalApi", () => ({
  runEmotionEval: vi.fn(),
}));

const completedResult = {
  session_id: "eval_test",
  status: "completed" as const,
  turns: [{ round: 1, user: "我很焦虑", assistant: "我听见你很焦虑。" }],
  scores: [{ name: "empathy", score: 0.8, reason: "ok", evidence: ["第 1 轮"] }],
  summary: {
    overall_score: 0.8,
    verdict: "pass" as const,
    conclusion: "情绪支持稳定。",
    improvement_suggestions: ["继续观察更多场景。"],
  },
};

afterEach(() => {
  vi.clearAllMocks();
});

function getSubmittedRequest(callIndex = 0): EmotionEvalRequest {
  const request = vi.mocked(runEmotionEval).mock.calls[callIndex]?.[0];
  expect(request).toBeDefined();
  return request as EmotionEvalRequest;
}

describe("TestPanel", () => {
  it("renders scenario controls", () => {
    render(<TestPanel />);

    expect(screen.getByLabelText("用户背景")).toBeInTheDocument();
    expect(screen.getByLabelText("初始心情")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始测试" })).toBeInTheDocument();
  });

  it("submits scenario and renders result", async () => {
    vi.mocked(runEmotionEval).mockResolvedValue(completedResult);

    render(<TestPanel />);
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(screen.getByText("情绪支持稳定。")).toBeInTheDocument();
    });
    expect(screen.getByText("我很焦虑")).toBeInTheDocument();
  });

  it("clamps submitted rounds to the maximum value", async () => {
    vi.mocked(runEmotionEval).mockResolvedValue(completedResult);

    render(<TestPanel />);
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "9" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(runEmotionEval).toHaveBeenCalledWith(
        expect.objectContaining({
          rounds: 8,
        }),
      );
    });
  });

  it("clamps submitted rounds to the minimum value", async () => {
    vi.mocked(runEmotionEval).mockResolvedValue(completedResult);

    render(<TestPanel />);
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(runEmotionEval).toHaveBeenCalled();
    });
    expect(getSubmittedRequest().rounds).toBe(1);
  });

  it("does not submit NaN when rounds input is cleared", async () => {
    vi.mocked(runEmotionEval).mockResolvedValue(completedResult);

    render(<TestPanel />);
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(runEmotionEval).toHaveBeenCalled();
    });
    const { rounds } = getSubmittedRequest();
    expect(Number.isFinite(rounds)).toBe(true);
    expect(rounds).toBeGreaterThanOrEqual(1);
    expect(rounds).toBeLessThanOrEqual(8);
  });

  it("clears stale result when a rerun fails", async () => {
    vi.mocked(runEmotionEval)
      .mockResolvedValueOnce(completedResult)
      .mockRejectedValueOnce(new Error("评测服务不可用"));

    render(<TestPanel />);
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(screen.getByText("情绪支持稳定。")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(screen.getByText("评测服务不可用")).toBeInTheDocument();
    });
    expect(screen.queryByText("情绪支持稳定。")).not.toBeInTheDocument();
  });

  it("clears stale error when a rerun succeeds", async () => {
    vi.mocked(runEmotionEval)
      .mockRejectedValueOnce(new Error("评测服务不可用"))
      .mockResolvedValueOnce(completedResult);

    render(<TestPanel />);
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(screen.getByText("评测服务不可用")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(screen.getByText("情绪支持稳定。")).toBeInTheDocument();
    });
    expect(screen.queryByText("评测服务不可用")).not.toBeInTheDocument();
  });
});
