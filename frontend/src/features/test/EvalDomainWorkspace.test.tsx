import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EvalRunProvider } from "@/features/test/EvalRunProvider";

import { EvalDomainWorkspace } from "./EvalDomainWorkspace";

vi.mock("@/services/eval/scenarioApi", () => ({
  listScenarios: vi.fn().mockResolvedValue([]),
  startScenarioEvalAsync: vi.fn(),
  cancelEvalRun: vi.fn(),
}));

vi.mock("@/services/eval/evalApi", () => ({
  startExploratoryEvalAsync: vi.fn(),
}));

function renderWorkspace(domainId: string): ReturnType<typeof render> {
  return render(
    <EvalRunProvider>
      <EvalDomainWorkspace
        coverageScore={0.5}
        domainId={domainId}
        domainLabel="测试域"
        passScore={0.8}
        onBack={vi.fn()}
      />
    </EvalRunProvider>,
  );
}

describe("EvalDomainWorkspace", () => {
  it("shows exploratory tab for emotion domain", () => {
    renderWorkspace("emotion");
    expect(screen.getByRole("tab", { name: "探索" })).toBeInTheDocument();
  });

  it("hides exploratory tab for non-emotion domains", () => {
    renderWorkspace("safety");
    expect(screen.queryByRole("tab", { name: "探索" })).not.toBeInTheDocument();
  });
});
