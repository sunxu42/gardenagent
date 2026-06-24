/** 界面文案本地化：将 API / 日志等领域的英文枚举映射为中文展示 */

const EVAL_TIER_LABELS: Record<string, string> = {
  all: "全部",
  smoke: "冒烟",
  judge: "评判",
  exploratory: "探索",
};

const RUN_STATUS_LABELS: Record<string, string> = {
  running: "运行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  pending: "等待中",
};

const ASSERTION_STATUS_LABELS: Record<string, string> = {
  pass: "通过",
  fail: "失败",
  skip: "跳过",
  warn: "警告",
};

const VERDICT_LABELS: Record<string, string> = {
  pass: "通过",
  fail: "失败",
  warning: "警告",
};

const LOG_LEVEL_LABELS: Record<string, string> = {
  DEBUG: "调试",
  INFO: "信息",
  WARNING: "警告",
  ERROR: "错误",
};

const LOG_MODULE_LABELS: Record<string, string> = {
  HANDLER: "消息处理",
  ASR: "语音识别",
  AGENT: "智能体",
  TTS: "语音合成",
  EMOTION: "情绪",
  TRANSPORT: "传输",
  METRICS: "指标",
  MEMORY: "记忆",
  SYSTEM: "系统",
};

const EVAL_PHASE_LABELS: Record<string, string> = {
  setup: "准备",
  agent: "对话",
  assertions: "断言",
  judge: "评判",
  starting: "启动",
  completed: "完成",
  idle: "空闲",
};

export function labelEvalTier(tier: string): string {
  return EVAL_TIER_LABELS[tier] ?? tier;
}

export function labelRunStatus(status: string): string {
  return RUN_STATUS_LABELS[status] ?? status;
}

export function labelAssertionStatus(status: string): string {
  return ASSERTION_STATUS_LABELS[status] ?? status;
}

export function labelVerdict(verdict: string): string {
  return VERDICT_LABELS[verdict] ?? verdict;
}

export function labelLogLevel(level: string): string {
  return LOG_LEVEL_LABELS[level] ?? level;
}

export function labelLogModule(module: string): string {
  return LOG_MODULE_LABELS[module] ?? module;
}

export function labelEvalPhase(phase: string): string {
  return EVAL_PHASE_LABELS[phase] ?? phase;
}

/** 时长展示：毫秒 / 秒 */
export function formatDurationZh(durationMs: number | null | undefined): string {
  if (durationMs === null || durationMs === undefined) {
    return "";
  }
  if (durationMs < 1000) {
    return `${durationMs} 毫秒`;
  }
  return `${Math.round(durationMs / 1000)} 秒`;
}
