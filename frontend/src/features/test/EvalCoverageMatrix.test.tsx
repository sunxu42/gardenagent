import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EvalCoverageMatrix } from "@/features/test/EvalCoverageMatrix";

const matrix = {
  generated_at: "2026-06-25T00:00:00+00:00",
  cells: Array.from({ length: 16 }, (_, index) => {
    const domains = [
      "emotion",
      "safety",
      "persona",
      "relationship",
      "memory",
      "tools",
      "dialogue",
      "transport",
    ] as const;
    const domain = domains[Math.floor(index / 2)] ?? "emotion";
    const tier = index % 2 === 0 ? ("smoke" as const) : ("judge" as const);
    const labels: Record<string, string> = {
      emotion: "情感支持",
      safety: "安全边界",
      persona: "人设一致",
      relationship: "关系演化",
      memory: "记忆",
      tools: "工具与任务",
      dialogue: "对话连贯",
      transport: "传输与性能",
    };
    return {
      domain,
      domain_label: labels[domain] ?? domain,
      tier,
      scenario_count: domain === "memory" ? 2 : 1,
      scenarios: [],
      tags_covered: ["happy_path"],
      tags_expected: ["happy_path"],
      tags_missing: [],
      last_run_at: null,
      pass_count: 0,
      fail_count: 0,
      pass_rate: null,
    };
  }),
  tag_coverage: [],
};

const baseProps = {
  matrix,
  loading: false,
  error: null,
  onReload: vi.fn(),
};

describe("EvalCoverageMatrix", () => {
  it("renders radar chart and selects a domain via vertex", () => {
    const onSelectDomain = vi.fn();
    const onEnterDomain = vi.fn();

    render(
      <EvalCoverageMatrix
        {...baseProps}
        selectedDomain={null}
        onEnterDomain={onEnterDomain}
        onSelectDomain={onSelectDomain}
      />,
    );

    expect(screen.getByLabelText("评测能力域雷达图")).toBeInTheDocument();

    const memoryButton = screen.getByRole("button", { name: /记忆/ });
    fireEvent.click(memoryButton);
    expect(onEnterDomain).toHaveBeenCalledWith("memory");
  });

  it("shows domain summary when domain is selected", () => {
    render(
      <EvalCoverageMatrix
        {...baseProps}
        selectedDomain="memory"
        onEnterDomain={vi.fn()}
        onSelectDomain={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "记忆" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "进入测试" })).toBeInTheDocument();
  });

  it("shows tooltip with coverage and pass rate on sector hover", async () => {
    render(
      <EvalCoverageMatrix
        {...baseProps}
        selectedDomain={null}
        onEnterDomain={vi.fn()}
        onSelectDomain={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("评测能力域雷达图")).toBeInTheDocument();

    const sectors = document.querySelectorAll(".eval-coverage-radar__sector-hit");
    expect(sectors.length).toBeGreaterThan(0);
    fireEvent.pointerEnter(sectors[0]!);
    fireEvent.pointerMove(sectors[0]!);

    const tooltip = await screen.findByRole("tooltip");
    expect(tooltip).toHaveTextContent("情感支持");
    expect(tooltip).toHaveTextContent("场景覆盖");
    expect(tooltip).toHaveTextContent("通过率");
  });
});
