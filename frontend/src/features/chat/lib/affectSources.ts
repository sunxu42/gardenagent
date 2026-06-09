import type { AffectTurnRecord } from "../types";
import {
  agentMoodLabel,
  empathyLabel,
  emotionIntensityLabel,
  inferUserMood,
  repairLabel,
  resolveAgentMood,
  stanceLabel,
} from "./affectPresentation";
import { formatAffectNum } from "./affectFormat";
import { VAD_DIMENSIONS, formatVadValue, vadDimensionVerbal } from "./vadDimensions";

export interface SourceItem {
  label: string;
  detail: string;
}

export function buildUserAffectSources(record: AffectTurnRecord): SourceItem[] {
  const items: SourceItem[] = [];
  const quote = (record.userText || "").trim();
  if (quote) {
    items.push({
      label: "你的话",
      detail: quote.length > 120 ? `${quote.slice(0, 120)}…` : quote,
    });
  }
  const cue = (record.interpersonalCue || "").trim();
  if (cue) {
    items.push({ label: "AI 解读", detail: cue });
  }
  const vadLines = VAD_DIMENSIONS.map((dim) => {
    const val = record.userAffectVad[dim.key];
    return `${dim.label} ${formatVadValue(val, dim)}（${vadDimensionVerbal(dim.key, val)}）`;
  });
  items.push({
    label: "情绪维度",
    detail: vadLines.join(" · "),
  });
  const mood = inferUserMood(record.userAffectVad);
  items.push({
    label: "综合感受",
    detail: `由愉悦度与能量感综合为「${mood.label}」`,
  });
  if (record.userWeight != null) {
    items.push({
      label: "判断把握",
      detail: `模型对本轮用户情绪的确信度约 ${formatAffectNum(record.userWeight * 100, 0)}%`,
    });
  }
  return items;
}

export function buildAgentAffectSources(record: AffectTurnRecord): SourceItem[] {
  const items: SourceItem[] = [];
  const resolved = resolveAgentMood(record);

  if (record.responsePolicy) {
    const p = record.responsePolicy;
    items.push({
      label: "回应策略",
      detail: `${empathyLabel(p.empathyMode)} · ${stanceLabel(p.stance)} · ${repairLabel(p.repairAction)} · 直接程度 ${formatAffectNum(p.directiveness * 100, 0)}%`,
    });
  }

  if (record.agentVadTarget) {
    const t = record.agentVadTarget;
    items.push({
      label: "合成目标语气",
      detail: `愉悦 ${formatAffectNum(t.v)} / 能量 ${formatAffectNum(t.a)} / 掌控 ${formatAffectNum(t.d)}${
        record.actuationWeight != null ? `（应用强度 ${formatAffectNum(record.actuationWeight * 100, 0)}%）` : ""
      }`,
    });
  }

  if (record.agentEmotion) {
    items.push({
      label: "情绪分类",
      detail: `投影为「${agentMoodLabel(record.agentEmotion)}」，强度 ${emotionIntensityLabel(record.emotionScale)}（7 类情绪模型）`,
    });
  } else if (resolved?.isEstimate && record.agentVadAfter) {
    items.push({
      label: "情绪推断",
      detail: `尚无分类标签，由当前语气维度推断为「${resolved.mood.label}」`,
    });
  }

  if (record.agentVadAfter) {
    const a = record.agentVadAfter;
    items.push({
      label: "状态机落地",
      detail: `更新后 Agent 语气：愉悦 ${formatAffectNum(a.v)} / 能量 ${formatAffectNum(a.a)} / 掌控 ${formatAffectNum(a.d)}`,
    });
  }

  if (record.relationship) {
    const r = record.relationship;
    items.push({
      label: "关系上下文",
      detail: `信任 ${formatAffectNum(r.trust * 100, 0)}% · 亲近 ${formatAffectNum(r.warmth * 100, 0)}% · 阶段 ${r.stage}`,
    });
  }

  if (items.length === 0) {
    items.push({ label: "等待", detail: "助手回应策略生成中…" });
  }

  return items;
}
