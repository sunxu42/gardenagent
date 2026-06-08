import type { VadPoint } from "../types";

/** 雷达轴顺序：V 顶、A 右下、D 左下 */
const AXIS_ANGLES = [-Math.PI / 2, Math.PI / 6, (5 * Math.PI) / 6];

const AXIS_KEYS: Array<keyof VadPoint> = ["v", "a", "d"];
const AXIS_LABELS = ["V", "A", "D"];

export function normalizeVad(p: VadPoint): VadPoint {
  return {
    v: (p.v + 1) / 2,
    a: Math.max(0, Math.min(1, p.a)),
    d: (p.d + 1) / 2,
  };
}

export function vadVertices(p: VadPoint, cx: number, cy: number, maxR: number): [number, number][] {
  const n = normalizeVad(p);
  const values = [n.v, n.a, n.d];
  return AXIS_ANGLES.map((angle, i) => {
    const r = values[i] * maxR;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)] as [number, number];
  });
}

export function polygonPathFromVertices(vertices: [number, number][]): string {
  if (vertices.length === 0) return "";
  const [first, ...rest] = vertices;
  return `M ${first[0]} ${first[1]} ${rest.map(([x, y]) => `L ${x} ${y}`).join(" ")} Z`;
}

export function deltaColor(delta: number): string {
  if (delta > 0) return "#ef4444";
  if (delta < 0) return "#10b981";
  return "#9ca3af";
}

export function getPrevAgentVad(item: VadPoint, delta: VadPoint): VadPoint {
  return {
    v: item.v - delta.v,
    a: item.a - delta.a,
    d: item.d - delta.d,
  };
}

function clampVadPoint(p: VadPoint): VadPoint {
  return {
    v: Math.max(-1, Math.min(1, p.v)),
    a: Math.max(0, Math.min(1, p.a)),
    d: Math.max(-1, Math.min(1, p.d)),
  };
}

export function amplifyVadDelta(
  prev: VadPoint,
  current: VadPoint,
  factor = 2.2,
  minVisualDelta = 0.02
): VadPoint {
  const delta = {
    v: current.v - prev.v,
    a: current.a - prev.a,
    d: current.d - prev.d,
  };
  const boosted = {
    v:
      delta.v === 0
        ? 0
        : Math.sign(delta.v) * Math.max(Math.abs(delta.v) * factor, minVisualDelta),
    a:
      delta.a === 0
        ? 0
        : Math.sign(delta.a) * Math.max(Math.abs(delta.a) * factor, minVisualDelta),
    d:
      delta.d === 0
        ? 0
        : Math.sign(delta.d) * Math.max(Math.abs(delta.d) * factor, minVisualDelta),
  };
  return clampVadPoint({
    v: prev.v + boosted.v,
    a: prev.a + boosted.a,
    d: prev.d + boosted.d,
  });
}

export const formatVad = (value: number) => value.toFixed(3);

export { AXIS_KEYS, AXIS_LABELS };
