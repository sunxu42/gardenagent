import type { EmotionEvalRequest, InitialMood } from "@/features/test/types";

export const DEFAULT_EXPLORATORY_FORM: EmotionEvalRequest = {
  background: "独居，最近工作压力大，睡眠质量下降。",
  initial_mood: "anxious",
  rounds: 5,
  goal: "评估助手的情绪支持质量",
};

export const MOOD_OPTIONS: Array<{ value: InitialMood; label: string }> = [
  { value: "anxious", label: "焦虑" },
  { value: "sad", label: "难过" },
  { value: "angry", label: "生气" },
  { value: "lonely", label: "孤独" },
  { value: "stressed", label: "压力大" },
  { value: "neutral", label: "平静" },
];

export function clampRounds(value: number, fallback = DEFAULT_EXPLORATORY_FORM.rounds): number {
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return Math.min(8, Math.max(1, Math.round(value)));
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "评测运行失败";
}
