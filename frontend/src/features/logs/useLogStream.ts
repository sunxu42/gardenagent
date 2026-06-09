import { useCallback, useState } from "react";
import type { LogEntry } from "./logTypes";

const MAX_ENTRIES = 500;

/**
 * 独立使用的日志流状态（主应用通过 chatReducer 管理，此处供测试或独立面板复用）。
 */
export function useLogStream() {
  const [entries, setEntries] = useState<LogEntry[]>([]);

  const append = useCallback((entry: LogEntry) => {
    setEntries((prev) => {
      const next = [...prev, entry];
      return next.length > MAX_ENTRIES ? next.slice(next.length - MAX_ENTRIES) : next;
    });
  }, []);

  const clear = useCallback(() => {
    setEntries([]);
  }, []);

  return { entries, append, clear };
}
