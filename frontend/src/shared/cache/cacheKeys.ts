export const CACHE_KEYS = {
  scenarios: "scenarios",
  promptTree: "prompt-tree",
} as const;

export function scenarioCacheKey(tier?: "smoke" | "judge"): string {
  if (!tier) {
    return CACHE_KEYS.scenarios;
  }
  return `scenarios:${tier}`;
}
