export const LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"] as const;
export type LogLevel = (typeof LOG_LEVELS)[number];

export const LOG_MODULES = [
  "HANDLER",
  "ASR",
  "AGENT",
  "TTS",
  "EMOTION",
  "TRANSPORT",
  "METRICS",
  "MEMORY",
  "SYSTEM",
] as const;
export type LogModule = (typeof LOG_MODULES)[number];

export interface LogEntry {
  id: string;
  tsMs: number;
  level: LogLevel;
  module: LogModule;
  message: string;
  turnId?: string;
  extra?: Record<string, unknown>;
}
