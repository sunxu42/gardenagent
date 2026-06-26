import type { EvalRunSummary, HistoryDomainFilter, HistoryTierFilter, ScenarioSummary } from "@/features/test/types";

export function buildScenarioDomainMap(scenarios: ScenarioSummary[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const scenario of scenarios) {
    map.set(scenario.id, scenario.domain);
    const shortId = scenario.id.split("/").pop();
    if (shortId) {
      map.set(shortId, scenario.domain);
    }
  }
  return map;
}

export function filterHistoryItems(
  items: EvalRunSummary[],
  tier: HistoryTierFilter,
  domain: HistoryDomainFilter,
  domainMap: Map<string, string>,
): EvalRunSummary[] {
  return items.filter((item) => {
    if (tier !== "all" && item.tier !== tier) {
      return false;
    }
    if (domain === "all") {
      return true;
    }
    if (item.tier === "exploratory" || item.mode === "exploratory") {
      return domain === "emotion";
    }
    const itemDomain = domainMap.get(item.scenario_id);
    return itemDomain === domain;
  });
}
