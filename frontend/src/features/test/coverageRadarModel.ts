import type { CoverageCell } from "@/features/test/types";

const DOMAIN_ORDER = [
  "emotion",
  "safety",
  "persona",
  "relationship",
  "memory",
  "tools",
  "dialogue",
  "transport",
] as const;

export interface DomainRadarPoint {
  domain: string;
  domain_label: string;
  coverage_score: number;
  pass_score: number;
  smoke: CoverageCell | null;
  judge: CoverageCell | null;
}

function groupCellsByDomain(cells: CoverageCell[]): Map<string, CoverageCell[]> {
  const grouped = new Map<string, CoverageCell[]>();
  for (const cell of cells) {
    const existing = grouped.get(cell.domain) ?? [];
    existing.push(cell);
    grouped.set(cell.domain, existing);
  }
  return grouped;
}

function computeCoverageScore(
  smoke: CoverageCell | null,
  judge: CoverageCell | null,
): number {
  const scenarioCount = (smoke?.scenario_count ?? 0) + (judge?.scenario_count ?? 0);
  if (scenarioCount === 0) {
    return 0;
  }

  const expected = new Set([
    ...(smoke?.tags_expected ?? []),
    ...(judge?.tags_expected ?? []),
  ]);
  const covered = new Set([
    ...(smoke?.tags_covered ?? []),
    ...(judge?.tags_covered ?? []),
  ]);

  if (expected.size === 0) {
    return 1;
  }
  let hits = 0;
  for (const tag of expected) {
    if (covered.has(tag)) {
      hits += 1;
    }
  }
  return hits / expected.size;
}

function computePassScore(smoke: CoverageCell | null, judge: CoverageCell | null): number {
  const rates: number[] = [];
  for (const cell of [smoke, judge]) {
    if (!cell || cell.scenario_count === 0) {
      continue;
    }
    if (cell.pass_rate != null) {
      rates.push(cell.pass_rate);
    }
  }
  if (rates.length === 0) {
    return 0;
  }
  return rates.reduce((sum, rate) => sum + rate, 0) / rates.length;
}

export function buildDomainRadarPoints(cells: CoverageCell[]): DomainRadarPoint[] {
  const grouped = groupCellsByDomain(cells);
  const domains = [
    ...DOMAIN_ORDER,
    ...[...grouped.keys()].filter(
      (id) => !DOMAIN_ORDER.includes(id as (typeof DOMAIN_ORDER)[number]),
    ),
  ];

  const points: DomainRadarPoint[] = [];
  for (const domain of domains) {
    const domainCells = grouped.get(domain);
    if (!domainCells) {
      continue;
    }
    const smoke = domainCells.find((cell) => cell.tier === "smoke") ?? null;
    const judge = domainCells.find((cell) => cell.tier === "judge") ?? null;
    points.push({
      domain,
      domain_label: smoke?.domain_label ?? judge?.domain_label ?? domain,
      coverage_score: computeCoverageScore(smoke, judge),
      pass_score: computePassScore(smoke, judge),
      smoke,
      judge,
    });
  }
  return points;
}

export function polarPoint(
  center: number,
  radius: number,
  index: number,
  total: number,
  value: number,
): { x: number; y: number } {
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  const distance = radius * Math.max(0, Math.min(1, value));
  return {
    x: center + distance * Math.cos(angle),
    y: center + distance * Math.sin(angle),
  };
}

export function polygonPoints(
  center: number,
  radius: number,
  points: DomainRadarPoint[],
  valueKey: "coverage_score" | "pass_score",
): string {
  return points
    .map((point, index) => {
      const { x, y } = polarPoint(center, radius, index, points.length, point[valueKey]);
      return `${x},${y}`;
    })
    .join(" ");
}

export function sectorPath(
  center: number,
  radius: number,
  index: number,
  total: number,
): string {
  const startAngle = (Math.PI * 2 * (index - 0.5)) / total - Math.PI / 2;
  const endAngle = (Math.PI * 2 * (index + 0.5)) / total - Math.PI / 2;
  const x1 = center + radius * Math.cos(startAngle);
  const y1 = center + radius * Math.sin(startAngle);
  const x2 = center + radius * Math.cos(endAngle);
  const y2 = center + radius * Math.sin(endAngle);
  return `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2} Z`;
}
