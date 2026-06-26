import { describe, expect, it, vi } from "vitest";

import { fetchCoverage } from "@/services/eval/coverageApi";

describe("fetchCoverage", () => {
  it("parses coverage matrix response", async () => {
    const payload = {
      generated_at: "2026-06-25T00:00:00+00:00",
      cells: [
        {
          domain: "memory",
          domain_label: "记忆",
          tier: "smoke",
          scenario_count: 2,
          scenarios: [],
          tags_covered: ["memory_recall"],
          tags_expected: ["memory_recall", "cross_session"],
          tags_missing: ["cross_session"],
          last_run_at: null,
          pass_count: 0,
          fail_count: 0,
          pass_rate: null,
        },
      ],
      tag_coverage: [],
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const matrix = await fetchCoverage();
    expect(matrix.cells).toHaveLength(1);
    expect(matrix.cells[0]?.domain).toBe("memory");

    vi.unstubAllGlobals();
  });
});
