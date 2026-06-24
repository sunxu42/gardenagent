import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { EmotionEvalRequest } from "@/features/test/types";
import { startExploratoryEvalAsync } from "@/services/eval/evalApi";

import { EvalRunProvider } from "./EvalRunProvider";
import { TestPanel } from "./TestPanel";

vi.mock("@/services/eval/evalApi", () => ({
  startExploratoryEvalAsync: vi.fn(),
}));

vi.mock("@/services/eval/scenarioApi", () => ({
  listScenarios: vi.fn().mockResolvedValue([]),
  startScenarioEvalAsync: vi.fn(),
  cancelEvalRun: vi.fn(),
  listEvalRuns: vi.fn().mockResolvedValue([]),
  getEvalRun: vi.fn(),
}));

function renderPanel(): ReturnType<typeof render> {
  return render(
    <EvalRunProvider>
      <TestPanel />
    </EvalRunProvider>,
  );
}

afterEach(() => {
  vi.clearAllMocks();
});

function getSubmittedRequest(callIndex = 0): EmotionEvalRequest {
  const request = vi.mocked(startExploratoryEvalAsync).mock.calls[callIndex]?.[0];
  expect(request).toBeDefined();
  return request as EmotionEvalRequest;
}

function openExploratoryTab(): void {
  fireEvent.click(screen.getByRole("tab", { name: "情绪探索" }));
}

describe("TestPanel", () => {
  it("renders scenario controls", () => {
    renderPanel();
    openExploratoryTab();

    expect(screen.getByLabelText("用户背景")).toBeInTheDocument();
    expect(screen.getByLabelText("初始心情")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始测试" })).toBeInTheDocument();
  });

  it("starts exploratory eval and shows progress header", async () => {
    vi.mocked(startExploratoryEvalAsync).mockResolvedValue({
      run_id: "eval_test",
      scenario_id: "exploratory",
      tier: "exploratory",
      status: "running",
    });

    renderPanel();
    openExploratoryTab();
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "取消测试" })).toBeInTheDocument();
      expect(screen.getByText("探索过程")).toBeInTheDocument();
    });
  });

  it("clamps submitted rounds to the maximum value", async () => {
    vi.mocked(startExploratoryEvalAsync).mockResolvedValue({
      run_id: "eval_test",
      scenario_id: "exploratory",
      tier: "exploratory",
      status: "running",
    });

    renderPanel();
    openExploratoryTab();
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "9" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          rounds: 8,
        }),
        expect.any(String),
      );
    });
  });

  it("clamps submitted rounds to the minimum value", async () => {
    vi.mocked(startExploratoryEvalAsync).mockResolvedValue({
      run_id: "eval_test",
      scenario_id: "exploratory",
      tier: "exploratory",
      status: "running",
    });

    renderPanel();
    openExploratoryTab();
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalled();
    });
    expect(getSubmittedRequest().rounds).toBe(1);
  });

  it("does not submit NaN when rounds input is cleared", async () => {
    vi.mocked(startExploratoryEvalAsync).mockResolvedValue({
      run_id: "eval_test",
      scenario_id: "exploratory",
      tier: "exploratory",
      status: "running",
    });

    renderPanel();
    openExploratoryTab();
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalled();
    });
    const { rounds } = getSubmittedRequest();
    expect(Number.isFinite(rounds)).toBe(true);
    expect(rounds).toBeGreaterThanOrEqual(1);
    expect(rounds).toBeLessThanOrEqual(8);
  });

});
