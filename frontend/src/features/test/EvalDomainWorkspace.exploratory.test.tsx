import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { EmotionEvalRequest } from "@/features/test/types";
import { startExploratoryEvalAsync } from "@/services/eval/evalApi";

import { EvalRunProvider } from "./EvalRunProvider";
import { EvalDomainWorkspace } from "./EvalDomainWorkspace";

vi.mock("@/services/eval/evalApi", () => ({
  startExploratoryEvalAsync: vi.fn(),
}));

vi.mock("@/services/eval/scenarioApi", () => ({
  listScenarios: vi.fn().mockResolvedValue([]),
  startScenarioEvalAsync: vi.fn(),
  cancelEvalRun: vi.fn(),
}));

function renderEmotionWorkspace(): ReturnType<typeof render> {
  return render(
    <EvalRunProvider>
      <EvalDomainWorkspace
        coverageScore={0.5}
        domainId="emotion"
        domainLabel="情感支持"
        passScore={0.8}
        onBack={vi.fn()}
      />
    </EvalRunProvider>,
  );
}

function openExploratoryTab(): void {
  fireEvent.click(screen.getByRole("tab", { name: "探索" }));
}

function getSubmittedRequest(callIndex = 0): EmotionEvalRequest {
  const request = vi.mocked(startExploratoryEvalAsync).mock.calls[callIndex]?.[0];
  expect(request).toBeDefined();
  return request as EmotionEvalRequest;
}

describe("EvalDomainWorkspace exploratory", () => {
  it("renders exploratory controls in emotion domain", () => {
    renderEmotionWorkspace();
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

    renderEmotionWorkspace();
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

    renderEmotionWorkspace();
    openExploratoryTab();
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "9" } });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalledWith(
        expect.objectContaining({ rounds: 8 }),
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

    renderEmotionWorkspace();
    openExploratoryTab();
    fireEvent.change(screen.getByLabelText("测试轮次"), { target: { value: "0" } });
    await waitFor(() => {
      expect(screen.getByLabelText("测试轮次")).toHaveValue(1);
    });
    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));

    await waitFor(() => {
      expect(startExploratoryEvalAsync).toHaveBeenCalledWith(
        expect.objectContaining({ rounds: 1 }),
        expect.any(String),
      );
    });
  });
});
