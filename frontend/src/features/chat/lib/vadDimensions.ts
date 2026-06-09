import type { VadPoint } from "../types";
import { formatAffectNum } from "./affectFormat";

export interface VadDimensionMeta {
  key: keyof VadPoint;
  label: string;
  hint: string;
  min: number;
  max: number;
  bipolar: boolean;
}

export const VAD_DIMENSIONS: VadDimensionMeta[] = [
  {
    key: "v",
    label: "愉悦度",
    hint: "消极 ← → 积极",
    min: -1,
    max: 1,
    bipolar: true,
  },
  {
    key: "a",
    label: "能量感",
    hint: "平静 ← → 激动",
    min: 0,
    max: 1,
    bipolar: false,
  },
  {
    key: "d",
    label: "掌控感",
    hint: "被动 ← → 强势",
    min: -1,
    max: 1,
    bipolar: true,
  },
];

export function vadValueToPercent(value: number, dim: VadDimensionMeta): number {
  const clamped = Math.max(dim.min, Math.min(dim.max, value));
  if (dim.bipolar) {
    return ((clamped - dim.min) / (dim.max - dim.min)) * 100;
  }
  return (clamped / dim.max) * 100;
}

export function formatVadValue(value: number, dim: VadDimensionMeta): string {
  return formatAffectNum(value, dim.bipolar ? 2 : 2);
}

export function vadDimensionVerbal(key: keyof VadPoint, value: number): string {
  if (key === "v") {
    if (value > 0.35) return "偏积极";
    if (value < -0.35) return "偏消极";
    return "较中性";
  }
  if (key === "a") {
    if (value > 0.65) return "较激动";
    if (value < 0.35) return "较平静";
    return "适中";
  }
  if (value > 0.35) return "偏强势";
  if (value < -0.35) return "偏被动";
  return "较中性";
}
