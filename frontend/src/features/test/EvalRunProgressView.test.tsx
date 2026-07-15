import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import type { LiveEvalRunState } from "@/features/test/evalRunStore";

function buildState(
  overrides: Partial<Pick<LiveEvalRunState, "status" | "phase" | "timeline" | "progressMessage">>,
): Pick<
  LiveEvalRunState,
  | "status"
  | "progressMessage"
  | "phase"
  | "agentProgress"
  | "judgeProgress"
  | "timeline"
  | "scenarioId"
  | "tier"
> {
  return {
    status: "completed",
    progressMessage: "评测已完成",
    phase: "completed",
    agentProgress: null,
    judgeProgress: null,
    timeline: [{ id: "tl-1", at: 0, tone: "success", title: "评测已完成" }],
    scenarioId: "exploratory",
    tier: "exploratory",
    ...overrides,
  };
}

describe("EvalRunProgressView", () => {
  it("shows success icon on the completed step after a live run finishes", () => {
    const { container } = render(<EvalRunProgressView state={buildState({})} />);

    expect(screen.getByText("完成")).toBeInTheDocument();
    const completedStep = screen.getByText("完成").closest("div");
    expect(completedStep?.querySelector(".test-text-pass")).toBeTruthy();
    expect(container.querySelectorAll(".test-text-pass").length).toBeGreaterThanOrEqual(5);
  });

  it("shows failure icon on the completed step when the run failed", () => {
    render(
      <EvalRunProgressView
        state={buildState({
          status: "failed",
          phase: "failed",
          progressMessage: "评测未通过",
        })}
      />,
    );

    const completedStep = screen.getByText("完成").closest("div");
    expect(completedStep?.querySelector(".test-text-fail")).toBeTruthy();
  });
});
