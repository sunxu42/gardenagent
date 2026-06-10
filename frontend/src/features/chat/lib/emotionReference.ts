import type { VadPoint } from "../types";
import { agentMoodLabel, relationshipStageLabel } from "./affectPresentation";
import { formatVadTriple } from "./affectFormat";

/** 与 yard/emotion/core/vad.py EMOTION_PROTOTYPES 对齐 */
export interface EmotionPrototype {
  id: string;
  vad: VadPoint;
  /** 助手语气 / TTS 侧的典型表达 */
  expression: string;
}

export const EMOTION_PROTOTYPES: EmotionPrototype[] = [
  {
    id: "happy",
    vad: { v: 0.8, a: 0.7, d: 0.5 },
    expression: "语调明亮、节奏略快，愿意分享与鼓励。",
  },
  {
    id: "surprised",
    vad: { v: 0.1, a: 0.8, d: -0.1 },
    expression: "短促上扬、停顿明显，表达意外或好奇。",
  },
  {
    id: "neutral",
    vad: { v: 0, a: 0.3, d: 0 },
    expression: "平稳克制，信息为主，不过度渲染情绪。",
  },
  {
    id: "sad",
    vad: { v: -0.7, a: 0.3, d: -0.5 },
    expression: "语速放缓、音量偏低，更多倾听与陪伴。",
  },
  {
    id: "fear",
    vad: { v: -0.6, a: 0.8, d: -0.7 },
    expression: "紧张、不确定，语气谨慎并反复确认。",
  },
  {
    id: "angry",
    vad: { v: -0.6, a: 0.8, d: 0.6 },
    expression: "重音加强、句短有力，但仍受策略层约束。",
  },
  {
    id: "hate",
    vad: { v: -0.7, a: 0.5, d: 0.2 },
    expression: "冷淡疏离，边界清晰，避免过度亲近。",
  },
];

export interface RelationshipStageRef {
  id: string;
  label: string;
  /** 判定条件（与 derive_stage 一致） */
  criteria: string;
  /** 助手典型回应风格 */
  expression: string;
}

export const RELATIONSHIP_STAGE_REFS: RelationshipStageRef[] = [
  {
    id: "bonded",
    label: relationshipStageLabel("bonded"),
    criteria: "信任 ≥ 70% 且亲近 ≥ 70%",
    expression: "更敞开、更直接，可适度调侃与深聊。",
  },
  {
    id: "trusted",
    label: relationshipStageLabel("trusted"),
    criteria: "信任 ≥ 70%",
    expression: "可靠稳重，愿意给建议，但仍保留分寸。",
  },
  {
    id: "familiar",
    label: relationshipStageLabel("familiar"),
    criteria: "亲近 ≥ 60%",
    expression: "语气随和温暖，减少客套与距离感。",
  },
  {
    id: "stranger",
    label: relationshipStageLabel("stranger"),
    criteria: "信任与亲近均 < 30%",
    expression: "礼貌克制，少追问隐私，多确认意图。",
  },
  {
    id: "acquaintance",
    label: relationshipStageLabel("acquaintance"),
    criteria: "其余默认区间",
    expression: "友好但中性，逐步建立熟悉感。",
  },
];

export function formatEmotionVad(id: string): string {
  const proto = EMOTION_PROTOTYPES.find((e) => e.id === id);
  if (!proto) return "—";
  return formatVadTriple(proto.vad);
}

export function emotionDisplayLabel(id: string): string {
  return agentMoodLabel(id);
}
