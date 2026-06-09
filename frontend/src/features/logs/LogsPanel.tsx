import { useEffect, useMemo, useRef, useState } from "react";
import type { LogEntry, LogLevel } from "./logTypes";
import { LogLine } from "./LogLine";
import "./logs-panel.css";

const LEVEL_RANK: Record<LogLevel, number> = {
  DEBUG: 10,
  INFO: 20,
  WARNING: 30,
  ERROR: 40,
};

export interface LogsPanelProps {
  entries: LogEntry[];
  onClear?: () => void;
}

export function LogsPanel({ entries, onClear }: LogsPanelProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const [minLevel, setMinLevel] = useState<LogLevel>("INFO");
  const [autoScroll, setAutoScroll] = useState(true);

  const visibleEntries = useMemo(
    () => entries.filter((entry) => LEVEL_RANK[entry.level] >= LEVEL_RANK[minLevel]),
    [entries, minLevel],
  );

  useEffect(() => {
    if (!autoScroll || !listRef.current) {
      return;
    }
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [visibleEntries.length, autoScroll]);

  return (
    <section className="logs-panel" aria-label="会话日志">
      <header className="logs-panel__toolbar">
        <h2 className="logs-panel__title">日志</h2>
        <span className="logs-panel__count">
          {visibleEntries.length}/{entries.length}
        </span>
        <div className="logs-panel__actions">
          <button
            type="button"
            className={`logs-panel__btn${minLevel === "DEBUG" ? " logs-panel__btn--active" : ""}`}
            onClick={() => setMinLevel((prev) => (prev === "DEBUG" ? "INFO" : "DEBUG"))}
          >
            {minLevel === "DEBUG" ? "隐藏 DEBUG" : "显示 DEBUG"}
          </button>
          <button
            type="button"
            className={`logs-panel__btn${autoScroll ? " logs-panel__btn--active" : ""}`}
            onClick={() => setAutoScroll((v) => !v)}
          >
            {autoScroll ? "暂停滚动" : "自动滚动"}
          </button>
          <button type="button" className="logs-panel__btn" onClick={() => onClear?.()}>
            清空
          </button>
        </div>
      </header>
      <div ref={listRef} className="logs-panel__list" role="log" aria-live="polite">
        {visibleEntries.length === 0 ? (
          <p className="logs-panel__empty">
            {entries.length === 0 ? "暂无日志，开始对话后将显示当前会话日志。" : "当前筛选条件下无日志。"}
          </p>
        ) : (
          visibleEntries.map((entry) => <LogLine key={entry.id} entry={entry} />)
        )}
      </div>
    </section>
  );
}
