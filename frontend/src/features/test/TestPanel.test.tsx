import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

vi.mock("@/services/eval/coverageApi", () => ({
  fetchCoverage: vi.fn().mockResolvedValue({
    generated_at: "2026-06-25T00:00:00+00:00",
    cells: [],
    tag_coverage: [],
  }),
}));

function renderPanel(): ReturnType<typeof render> {
  return render(
    <EvalRunProvider>
      <TestPanel />
    </EvalRunProvider>,
  );
}

describe("TestPanel", () => {
  it("renders only overview and history tabs", () => {
    renderPanel();

    expect(screen.getByRole("tab", { name: "总览" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "运行历史" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "场景回归" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "情绪探索" })).not.toBeInTheDocument();
  });

  it("switches to history tab", () => {
    renderPanel();
    fireEvent.click(screen.getByRole("tab", { name: "运行历史" }));
    expect(screen.getByText("历史列表")).toBeInTheDocument();
  });
});
