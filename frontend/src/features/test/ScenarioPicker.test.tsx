import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ScenarioSummary } from "@/features/test/types";
import { clearAllCaches } from "@/shared/cache/cacheStore";
import { listScenarios } from "@/services/eval/scenarioApi";

import { ScenarioPicker } from "./ScenarioPicker";

vi.mock("@/services/eval/scenarioApi", () => ({
  listScenarios: vi.fn(),
}));

const scenarios: ScenarioSummary[] = [
  { id: "greeting_01", description: "greeting", domain: "smoke", tier: "smoke" },
  { id: "tool_status_01", description: "tool", domain: "smoke", tier: "smoke" },
];

const domainScenarios: ScenarioSummary[] = [
  { id: "smoke/emotion_a", description: "a", domain: "emotion", tier: "smoke" },
  { id: "smoke/safety_a", description: "b", domain: "safety", tier: "smoke" },
];

describe("ScenarioPicker", () => {
  beforeEach(() => {
    sessionStorage.clear();
    clearAllCaches();
  });

  it("toggles between select all and clear", async () => {
    const onChange = vi.fn();
    vi.mocked(listScenarios).mockResolvedValue(scenarios);

    const { rerender } = render(
      <ScenarioPicker selectedIds={[]} tier="smoke" onChange={onChange} />,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "全选当前列表" })).toBeInTheDocument();
    });
    expect(screen.getByText("勾选要运行的场景")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "全选当前列表" }));
    expect(onChange).toHaveBeenCalledWith(["greeting_01", "tool_status_01"]);

    rerender(
      <ScenarioPicker
        selectedIds={["greeting_01", "tool_status_01"]}
        tier="smoke"
        onChange={onChange}
      />,
    );

    expect(screen.getByRole("button", { name: "清空已选场景" })).toBeInTheDocument();
    expect(screen.getByText("已选 2 项")).toBeInTheDocument();
  });

  it("filters scenarios by domain", async () => {
    vi.mocked(listScenarios).mockResolvedValue(domainScenarios);
    const onChange = vi.fn();
    render(
      <ScenarioPicker domain="emotion" selectedIds={[]} tier="smoke" onChange={onChange} />,
    );

    await waitFor(() => {
      expect(screen.getByText("smoke/emotion_a")).toBeInTheDocument();
    });
    expect(screen.queryByText("smoke/safety_a")).not.toBeInTheDocument();
  });
});
