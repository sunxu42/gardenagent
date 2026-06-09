import type { AffectTurnRecord, RelationshipSnapshot, ResponsePolicySnapshot, VadPoint } from "../types";

export type MoodTone = "positive" | "neutral" | "negative" | "tense";

export interface MoodPresentation {
  label: string;
  tone: MoodTone;
}

const AGENT_MOOD_LABELS: Record<string, string> = {
  happy: "开心",
  sad: "悲伤",
  angry: "生气",
  fear: "害怕",
  surprised: "惊讶",
  disgust: "厌恶",
  neutral: "平和",
};

const STAGE_LABELS: Record<string, string> = {
  stranger: "陌生",
  acquaintance: "相识",
  familiar: "熟悉",
  trusted: "信任",
  bonded: "亲密",
};

const EMPATHY_LABELS: Record<string, string> = {
  neutral: "平稳回应",
  acknowledge_first: "先倾听理解",
  mirror_warmth: "温暖共鸣",
  de_escalate: "缓和情绪",
  celebrate_with: "一起分享喜悦",
};

const STANCE_LABELS: Record<string, string> = {
  balanced: "均衡语气",
  calm_professional: "冷静专业",
  warm_casual: "亲切随和",
  guarded_formal: "谨慎正式",
};

const REPAIR_LABELS: Record<string, string> = {
  none: "无需特别安抚",
  apologize_if_mistake: "如有误会会致歉",
  clarify_before_advise: "先澄清再给建议",
};

export function agentMoodLabel(emotion?: string): string {
  if (!emotion) return "平和";
  return AGENT_MOOD_LABELS[emotion] ?? emotion;
}

export function relationshipStageLabel(stage?: string): string {
  if (!stage) return "相识";
  return STAGE_LABELS[stage] ?? stage;
}

export function empathyLabel(mode?: string): string {
  if (!mode) return "平稳回应";
  return EMPATHY_LABELS[mode] ?? mode;
}

export function stanceLabel(stance?: string): string {
  if (!stance) return "均衡语气";
  return STANCE_LABELS[stance] ?? stance;
}

export function repairLabel(action?: string): string {
  if (!action) return "无需特别安抚";
  return REPAIR_LABELS[action] ?? action;
}

/** 由用户 VAD 推断可读感受（无后端标签时的轻量投影） */
export function inferUserMood(vad: VadPoint): MoodPresentation {
  const { v, a } = vad;
  if (v < -0.4 && a > 0.55) return { label: "有些烦躁", tone: "tense" };
  if (v < -0.35) return { label: "情绪低落", tone: "negative" };
  if (v > 0.4 && a > 0.6) return { label: "兴奋开心", tone: "positive" };
  if (v > 0.3) return { label: "心情不错", tone: "positive" };
  if (a > 0.65) return { label: "有些紧张", tone: "tense" };
  if (a < 0.35 && Math.abs(v) < 0.25) return { label: "平静放松", tone: "neutral" };
  return { label: "比较平静", tone: "neutral" };
}

export function agentMoodPresentation(record: AffectTurnRecord): MoodPresentation {
  const label = agentMoodLabel(record.agentEmotion);
  const emotion = record.agentEmotion ?? "neutral";
  if (emotion === "happy" || emotion === "surprised") return { label, tone: "positive" };
  if (emotion === "sad" || emotion === "disgust") return { label, tone: "negative" };
  if (emotion === "angry" || emotion === "fear") return { label, tone: "tense" };
  return { label, tone: "neutral" };
}

export interface ResolvedAgentMood {
  mood: MoodPresentation;
  intensity?: string;
  /** 由 VAD 推断，尚无投影标签 */
  isEstimate: boolean;
}

/** 助手语气：优先 emotion 标签，否则从 VAD after/target 推断 */
export function resolveAgentMood(record: AffectTurnRecord): ResolvedAgentMood | null {
  if (record.agentEmotion) {
    return {
      mood: agentMoodPresentation(record),
      intensity: emotionIntensityLabel(record.emotionScale),
      isEstimate: false,
    };
  }
  const vad = record.agentVadAfter ?? record.agentVadTarget;
  if (vad) {
    return {
      mood: inferUserMood(vad),
      intensity: record.agentVadAfter
        ? emotionIntensityLabel(record.emotionScale)
        : "预期",
      isEstimate: true,
    };
  }
  return null;
}

export function moodToneClasses(tone: MoodTone): { badge: string; dot: string } {
  switch (tone) {
    case "positive":
      return {
        badge: "bg-emerald-500/12 text-emerald-800 border-emerald-500/25 dark:text-emerald-200",
        dot: "bg-emerald-500",
      };
    case "negative":
      return {
        badge: "bg-violet-500/12 text-violet-900 border-violet-500/25 dark:text-violet-200",
        dot: "bg-violet-500",
      };
    case "tense":
      return {
        badge: "bg-amber-500/12 text-amber-900 border-amber-500/25 dark:text-amber-100",
        dot: "bg-amber-500",
      };
    default:
      return {
        badge: "bg-muted text-muted-foreground border-border",
        dot: "bg-muted-foreground/60",
      };
  }
}

export function percent01(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value * 100)));
}

export function relationshipDeltaSummary(rel?: RelationshipSnapshot): string | null {
  if (!rel?.trustDelta && !rel?.warmthDelta) return null;
  const parts: string[] = [];
  const td = rel.trustDelta ?? 0;
  const wd = rel.warmthDelta ?? 0;
  if (Math.abs(td) >= 0.01) {
    parts.push(td > 0 ? "信任感上升" : "信任感下降");
  }
  if (Math.abs(wd) >= 0.01) {
    parts.push(wd > 0 ? "更亲近了" : "距离感增加");
  }
  return parts.length ? parts.join("，") : null;
}

export function responseStrategySummary(policy?: ResponsePolicySnapshot): string {
  if (!policy) return "自然对话";
  return empathyLabel(policy.empathyMode);
}

/** 本轮助手回应态度（策略层立场 + 共情方式） */
export function resolveAttitudeSummary(record: AffectTurnRecord): string {
  if (record.responsePolicy) {
    const p = record.responsePolicy;
    return `${stanceLabel(p.stance)} · ${empathyLabel(p.empathyMode)}`;
  }
  const agent = resolveAgentMood(record);
  return agent?.mood.label ?? "等待策略";
}

export function emotionIntensityLabel(scale?: number): string {
  if (scale == null) return "适中";
  if (scale <= 2) return "轻微";
  if (scale <= 4) return "适中";
  if (scale <= 6) return "明显";
  return "强烈";
}
