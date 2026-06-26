import type { VadPoint } from "../types";
import { formatAffectNum } from "./affectFormat";

export interface VadDimensionMeta {
  key: keyof VadPoint;
  /** 短标签 V / A / D，用于大部分界面 */
  shortLabel: string;
  /** 英文全称 Valence / Arousal / Dominance，用于情绪三维度引导页 */
  fullName: string;
  hint: string;
  /** 轴两端语义标签 */
  poleLow: string;
  poleHigh: string;
  /** 引导说明中的简短释义 */
  description: string;
  min: number;
  max: number;
  bipolar: boolean;
}

export const VAD_DIMENSIONS: VadDimensionMeta[] = [
  {
    key: "v",
    shortLabel: "V",
    fullName: "Valence",
    hint: "消极 ← → 积极",
    poleLow: "消极",
    poleHigh: "积极",
    description: "衡量情绪的积极或消极倾向，影响对你当下感受的判断。",
    min: -1,
    max: 1,
    bipolar: true,
  },
  {
    key: "a",
    shortLabel: "A",
    fullName: "Arousal",
    hint: "平静 ← → 激动",
    poleLow: "平静",
    poleHigh: "激动",
    description: "衡量生理与心理的激活程度，高能量常对应紧张、兴奋或焦躁。",
    min: 0,
    max: 1,
    bipolar: false,
  },
  {
    key: "d",
    shortLabel: "D",
    fullName: "Dominance",
    hint: "被动 ← → 强势",
    poleLow: "被动",
    poleHigh: "强势",
    description: "衡量自信与掌控感，影响语气是坚定推进还是退让回避。",
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
