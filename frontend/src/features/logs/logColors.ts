import type { LogLevel, LogModule } from "./logTypes";

/** 与 yard/observability/logging/modules.py 保持一致 */
export const MODULE_SHORT: Record<LogModule, string> = {
  HANDLER: "处理",
  ASR: "语音",
  AGENT: "智能",
  TTS: "合成",
  EMOTION: "情绪",
  TRANSPORT: "传输",
  METRICS: "指标",
  MEMORY: "记忆",
  SYSTEM: "系统",
};

export const MODULE_COLORS: Record<LogModule, string> = {
  HANDLER: "#22d3ee",
  ASR: "#60a5fa",
  AGENT: "#a78bfa",
  TTS: "#fb923c",
  EMOTION: "#f472b6",
  TRANSPORT: "#94a3b8",
  METRICS: "#34d399",
  MEMORY: "#fbbf24",
  SYSTEM: "#e2e8f0",
};

export const LEVEL_COLORS: Record<LogLevel, string> = {
  DEBUG: "#94a3b8",
  INFO: "#e2e8f0",
  WARNING: "#fbbf24",
  ERROR: "#f87171",
};
