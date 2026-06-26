import { describe, expect, it } from "vitest";

import { buildDomainRadarPoints } from "@/features/test/coverageRadarModel";
import type { CoverageCell } from "@/features/test/types";

function cell(
  domain: string,
  tier: "smoke" | "judge",
  overrides: Partial<CoverageCell> = {},
): CoverageCell {
  return {
    domain,
    domain_label: domain,
    tier,
    scenario_count: 1,
    scenarios: [],
    tags_covered: ["happy_path"],
    tags_expected: ["happy_path", "multi_turn"],
    tags_missing: ["multi_turn"],
    last_run_at: null,
    pass_count: 1,
    fail_count: 0,
    pass_rate: 1,
    ...overrides,
  };
}

describe("buildDomainRadarPoints", () => {
  it("returns eight domain points from matrix cells", () => {
    const domains = [
      "emotion",
      "safety",
      "persona",
      "relationship",
      "memory",
      "tools",
      "dialogue",
      "transport",
    ];
    const cells = domains.flatMap((domain) => [
      cell(domain, "smoke"),
      cell(domain, "judge"),
    ]);
    const points = buildDomainRadarPoints(cells);
    expect(points).toHaveLength(8);
  });

  it("computes coverage and pass scores", () => {
    const points = buildDomainRadarPoints([
      cell("memory", "smoke", {
        domain_label: "记忆",
        tags_covered: ["memory_recall"],
        tags_expected: ["memory_recall", "cross_session"],
        tags_missing: ["cross_session"],
        pass_rate: 0.5,
      }),
      cell("memory", "judge", {
        domain_label: "记忆",
        scenario_count: 0,
        tags_covered: [],
        tags_expected: ["memory_recall"],
        tags_missing: ["memory_recall"],
        pass_rate: null,
        pass_count: 0,
        fail_count: 0,
      }),
    ]);

    expect(points[0]?.domain_label).toBe("记忆");
    expect(points[0]?.coverage_score).toBe(0.5);
    expect(points[0]?.pass_score).toBe(0.5);
  });
});
