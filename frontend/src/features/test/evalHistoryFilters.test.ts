import { describe, expect, it } from "vitest";

import {
  buildScenarioDomainMap,
  filterHistoryItems,
} from "@/features/test/evalHistoryFilters";
import type { EvalRunSummary, ScenarioSummary } from "@/features/test/types";

const scenarios: ScenarioSummary[] = [
  { id: "smoke/emotion_a", description: "a", domain: "emotion", tier: "smoke" },
  { id: "judge/safety_b", description: "b", domain: "safety", tier: "judge" },
];

const items: EvalRunSummary[] = [
  {
    run_id: "1",
    scenario_id: "smoke/emotion_a",
    tier: "smoke",
    status: "completed",
  },
  {
    run_id: "2",
    scenario_id: "judge/safety_b",
    tier: "judge",
    status: "completed",
  },
  {
    run_id: "3",
    scenario_id: "exploratory",
    tier: "exploratory",
    mode: "exploratory",
    status: "completed",
  },
];

describe("evalHistoryFilters", () => {
  it("builds domain map with full and short ids", () => {
    const map = buildScenarioDomainMap(scenarios);
    expect(map.get("smoke/emotion_a")).toBe("emotion");
    expect(map.get("emotion_a")).toBe("emotion");
    expect(map.get("judge/safety_b")).toBe("safety");
  });

  it("filters history by domain", () => {
    const map = buildScenarioDomainMap(scenarios);
    const emotionOnly = filterHistoryItems(items, "all", "emotion", map);
    expect(emotionOnly.map((item) => item.run_id)).toEqual(["1", "3"]);

    const safetyOnly = filterHistoryItems(items, "all", "safety", map);
    expect(safetyOnly.map((item) => item.run_id)).toEqual(["2"]);
  });

  it("filters history by tier and domain together", () => {
    const map = buildScenarioDomainMap(scenarios);
    const result = filterHistoryItems(items, "smoke", "emotion", map);
    expect(result.map((item) => item.run_id)).toEqual(["1"]);
  });
});
