import type { LogEntry, LogLevel, LogModule } from "./logTypes";

let localLogSeq = 0;

/** 前端本地产生的日志条目（如清空日志后的保留记录）。 */
export function createLocalLogEntry(
  message: string,
  options: {
    level?: LogLevel;
    module?: LogModule;
    extra?: Record<string, unknown>;
  } = {},
): LogEntry {
  localLogSeq += 1;
  return {
    id: `local-${Date.now()}-${localLogSeq}`,
    tsMs: Date.now(),
    level: options.level ?? "INFO",
    module: options.module ?? "SYSTEM",
    message,
    extra: options.extra,
  };
}

export function buildLogsClearedEntry(previousCount: number): LogEntry {
  const detail =
    previousCount > 0
      ? `会话日志已清空（已清除 ${previousCount} 条，保留此记录）`
      : "会话日志已清空（无历史条目，保留此记录）";
  return createLocalLogEntry(detail, {
    extra: { action: "clear_logs", cleared_count: previousCount },
  });
}

export const PENDING_LOG_AFTER_RELOAD_KEY = "gardenagent.pendingLogAfterReload.v1";

/** 页面 reload 前暂存日志，刷新后在日志面板恢复展示。 */
export function stashPendingLogAfterReload(entry: LogEntry): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    sessionStorage.setItem(PENDING_LOG_AFTER_RELOAD_KEY, JSON.stringify(entry));
  } catch {
    // ignore quota / private mode
  }
}

export function consumePendingLogAfterReload(): LogEntry | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = sessionStorage.getItem(PENDING_LOG_AFTER_RELOAD_KEY);
  if (!raw) {
    return null;
  }
  sessionStorage.removeItem(PENDING_LOG_AFTER_RELOAD_KEY);
  try {
    const parsed = JSON.parse(raw) as LogEntry;
    if (typeof parsed.message !== "string" || typeof parsed.tsMs !== "number") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function summarizeClearResult(result: Record<string, unknown> | undefined): string {
  const mem0 = result?.mem0;
  let mem0Part = "Mem0 —";
  if (mem0 && typeof mem0 === "object") {
    const m = mem0 as Record<string, unknown>;
    if (m.skipped) mem0Part = "Mem0 跳过";
    else if (m.cleared) mem0Part = "Mem0 已清";
    else if (m.error) mem0Part = "Mem0 失败";
  }
  const checkpoints = Number(result?.checkpoints ?? 0);
  const buffers = Number(result?.session_buffers ?? 0);
  const emotion = result?.emotion;
  let emotionN = 0;
  if (emotion && typeof emotion === "object") {
    emotionN = Number((emotion as Record<string, unknown>).reset_managers ?? 0);
  }
  return `${mem0Part}；checkpoint×${checkpoints}；session_buffer×${buffers}；emotion_reset×${emotionN}`;
}

export function buildUserDataClearedEntry(
  userId: string,
  result?: Record<string, unknown>,
): LogEntry {
  const summary = summarizeClearResult(result);
  return createLocalLogEntry(`用户数据已清空（${summary}）`, {
    extra: {
      action: "clear_user_data",
      user_id: userId,
      result: result ?? {},
    },
  });
}
