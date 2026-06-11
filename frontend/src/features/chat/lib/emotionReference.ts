import type { AffectLockState, RelationshipSnapshot, VadPoint } from "../types";
import { formatVadTriple } from "./affectFormat";
import { agentMoodLabel, moodToneClasses, relationshipStageLabel, type MoodTone } from "./affectPresentation";

/** 与 yard/emotion/core/vad.py EMOTION_PROTOTYPES 对齐 */
export interface EmotionPrototype {
  id: string;
  vad: VadPoint;
  /** 助手语气 / TTS 侧的典型表达 */
  expression: string;
}

export const DEFAULT_AGENT_EMOTION_ID = "neutral";

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

/** 与 yard/emotion/constants.py RELATIONSHIP_STAGE_PRESETS 对齐 */
export const RELATIONSHIP_STAGE_PRESETS: Record<string, { trust: number; warmth: number }> = {
  stranger: { trust: 0.2, warmth: 0.2 },
  acquaintance: { trust: 0.45, warmth: 0.45 },
  familiar: { trust: 0.5, warmth: 0.65 },
  trusted: { trust: 0.75, warmth: 0.5 },
  bonded: { trust: 0.8, warmth: 0.8 },
};

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
    criteria: "非陌生，且信任 < 70%、亲近 < 60%",
    expression: "友好但中性，逐步建立熟悉感。",
  },
];

/** 阶段锁定/展示用代表点，与 yard/emotion/constants.py RELATIONSHIP_STAGE_PRESETS 一致 */
export function formatRelationshipPreset(id: string): string {
  const preset = RELATIONSHIP_STAGE_PRESETS[id];
  if (!preset) {
    return "—";
  }
  const trust = Math.round(preset.trust * 100);
  const warmth = Math.round(preset.warmth * 100);
  return `信任 ${trust}% · 亲近 ${warmth}%`;
}

export function emotionPrototypeVad(id: string): VadPoint | null {
  return EMOTION_PROTOTYPES.find((emo) => emo.id === id)?.vad ?? null;
}

export function inferEmotionIdFromVad(vad: VadPoint | null | undefined): string | null {
  if (!vad) {
    return null;
  }
  let bestId: string | null = null;
  let bestDist = Number.POSITIVE_INFINITY;
  for (const proto of EMOTION_PROTOTYPES) {
    const dv = vad.v - proto.vad.v;
    const da = vad.a - proto.vad.a;
    const dd = vad.d - proto.vad.d;
    const dist = dv * dv + da * da + dd * dd;
    if (dist < bestDist) {
      bestDist = dist;
      bestId = proto.id;
    }
  }
  return bestId;
}

export function resolveLiveAgentEmotionId(
  agentEmotion: string | null | undefined,
  vad: VadPoint | null | undefined,
): string {
  if (agentEmotion) {
    return agentEmotion;
  }
  return inferEmotionIdFromVad(vad) ?? DEFAULT_AGENT_EMOTION_ID;
}

export function resolveDisplayRelationship(
  liveRelationship: RelationshipSnapshot | null | undefined,
  displayStageId: string | null | undefined,
  locked: boolean,
): RelationshipSnapshot | null {
  if (locked && displayStageId) {
    const preset = RELATIONSHIP_STAGE_PRESETS[displayStageId];
    if (preset) {
      return { trust: preset.trust, warmth: preset.warmth, stage: displayStageId };
    }
  }
  return liveRelationship ?? null;
}

export function resolveDisplayAgentVad(
  liveVad: VadPoint | null | undefined,
  displayEmotionId: string | null | undefined,
  locked: boolean,
): VadPoint | null {
  if (locked && displayEmotionId) {
    return emotionPrototypeVad(displayEmotionId) ?? liveVad ?? null;
  }
  if (liveVad) {
    return liveVad;
  }
  if (displayEmotionId) {
    return emotionPrototypeVad(displayEmotionId);
  }
  return emotionPrototypeVad(DEFAULT_AGENT_EMOTION_ID);
}

export function formatEmotionVad(id: string): string {
  const proto = EMOTION_PROTOTYPES.find((e) => e.id === id);
  if (!proto) return "—";
  return formatVadTriple(proto.vad);
}

export function emotionDisplayLabel(id: string): string {
  return agentMoodLabel(id);
}

export function emotionMoodTone(id: string): MoodTone {
  if (id === "happy" || id === "surprised") return "positive";
  if (id === "sad") return "negative";
  if (id === "angry" || id === "fear") return "tense";
  return "neutral";
}

export function emotionToneDotClass(id: string): string {
  return moodToneClasses(emotionMoodTone(id)).dot;
}

export function toggleAffectLockRef(
  dimension: "relationship" | "agent_vad",
  refId: string,
  current: AffectLockState,
): string | null {
  const slice = dimension === "relationship" ? current.relationship : current.agentVad;
  if (slice.locked && slice.refId === refId) {
    return null;
  }
  return refId;
}
