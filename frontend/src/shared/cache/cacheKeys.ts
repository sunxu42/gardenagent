export const CACHE_KEYS = {
  scenarios: "scenarios",
  promptTree: "prompt-tree",
  coverage: "coverage",
  evalRuns: "eval-runs",
} as const;

export function scenarioCacheKey(tier?: "smoke" | "judge"): string {
  if (!tier) {
    return CACHE_KEYS.scenarios;
  }
  return `scenarios:${tier}`;
}

export function evalRunsCacheKey(
  tier?: "smoke" | "judge" | "exploratory",
): string {
  if (!tier) {
    return CACHE_KEYS.evalRuns;
  }
  return `${CACHE_KEYS.evalRuns}:${tier}`;
}
