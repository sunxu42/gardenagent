import type { CoverageMatrix } from "@/features/test/types";

export async function fetchCoverage(): Promise<CoverageMatrix> {
  const response = await fetch("/api/eval/coverage");
  if (!response.ok) {
    throw new Error(`coverage fetch failed: ${response.status}`);
  }
  return (await response.json()) as CoverageMatrix;
}
