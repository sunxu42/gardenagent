import type { EmotionProfile, VadPoint } from "../types";

export const DEFAULT_USER_VAD_BASELINE: VadPoint = { v: 0, a: 0.2, d: 0 };

export const DEFAULT_EMOTION_PROFILE: EmotionProfile = {
  userVadBaseline: DEFAULT_USER_VAD_BASELINE,
  agentVadBaseline: { v: 0.3, a: 0.55, d: 0.1 },
  relationshipBaseline: { trust: 0.5, warmth: 0.4 },
  userAffect: { perTurnOnly: true },
  agentVad: { perTurnAlpha: 0.48, perTurnBeta: 0.01, timeTauSec: 14400 },
  relationship: { perTurnAlpha: 0.65, timeTauSec: 28800 },
};

function readNum(value: unknown): number | undefined {
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

function readVad(raw: unknown): VadPoint | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const v = readNum(o.v);
  const a = readNum(o.a);
  const d = readNum(o.d);
  if (v === undefined || a === undefined || d === undefined) return null;
  return { v, a, d };
}

export function parseEmotionProfile(raw: unknown): EmotionProfile | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const userVad = readVad(o.user_vad_baseline);
  const agentVad = readVad(o.agent_vad_baseline);
  const relBase = o.relationship_baseline;
  const userAffect = o.user_affect;
  const agentDecay = o.agent_vad;
  const relDecay = o.relationship;
  if (!userVad || !agentVad) return null;
  if (!relBase || typeof relBase !== "object") return null;

  const rel = relBase as Record<string, unknown>;
  const trust = readNum(rel.trust);
  const warmth = readNum(rel.warmth);
  if (trust === undefined || warmth === undefined) return null;

  const ua = userAffect && typeof userAffect === "object" ? (userAffect as Record<string, unknown>) : {};
  const ad = agentDecay && typeof agentDecay === "object" ? (agentDecay as Record<string, unknown>) : {};
  const rd = relDecay && typeof relDecay === "object" ? (relDecay as Record<string, unknown>) : {};

  const perTurnOnly = ua.per_turn_only === true || ua.ema_alpha === undefined;
  const perTurnAlpha = readNum(ad.per_turn_alpha);
  const perTurnBeta = readNum(ad.per_turn_beta);
  const timeTauSec = readNum(ad.time_tau_sec);
  const relAlpha = readNum(rd.per_turn_alpha);
  const relTauSec = readNum(rd.time_tau_sec);

  if (
    perTurnAlpha === undefined ||
    perTurnBeta === undefined ||
    timeTauSec === undefined ||
    relAlpha === undefined ||
    relTauSec === undefined
  ) {
    return null;
  }

  return {
    userVadBaseline: userVad,
    agentVadBaseline: agentVad,
    relationshipBaseline: { trust, warmth },
    userAffect: { perTurnOnly },
    agentVad: { perTurnAlpha, perTurnBeta, timeTauSec },
    relationship: { perTurnAlpha: relAlpha, timeTauSec: relTauSec },
  };
}

export function resolveEmotionProfile(
  profile: EmotionProfile | null | undefined,
  agentBaselineFallback?: VadPoint | null,
): EmotionProfile {
  const base = profile ?? DEFAULT_EMOTION_PROFILE;
  if (!agentBaselineFallback) return base;
  return {
    ...base,
    agentVadBaseline: agentBaselineFallback,
  };
}

/** 将秒数格式化为可读时长（中文） */
export function formatTauLabel(sec: number): string {
  if (!Number.isFinite(sec) || sec <= 0) return "—";
  if (sec >= 86400) {
    const days = sec / 86400;
    return days >= 2 ? `约 ${Math.round(days)} 天` : "约 1 天";
  }
  if (sec >= 3600) {
    const hours = sec / 3600;
    return hours >= 2 ? `约 ${Math.round(hours)} 小时` : "约 1 小时";
  }
  if (sec >= 60) {
    const mins = sec / 60;
    return mins >= 2 ? `约 ${Math.round(mins)} 分钟` : "约 1 分钟";
  }
  return `约 ${Math.round(sec)} 秒`;
}

export function formatPercent01(n: number, digits = 0): string {
  return `${(n * 100).toFixed(digits)}%`;
}
