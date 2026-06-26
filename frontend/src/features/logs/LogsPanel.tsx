import { useEffect, useMemo, useRef, useState } from "react";
import { ScrollText } from "lucide-react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";
import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import { RailPanelColumn } from "@/components/rail/RailPanelShell";
import { RailToolbarButton } from "@/components/rail/RailToolbarButton";

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
    <RailPanelColumn className="logs-panel" aria-label="会话日志">
      <RailPanelHeader
        icon={ScrollText}
        title="日志"
        titleTrailing={`${visibleEntries.length}/${entries.length}`}
        actions={
          <>
            <RailToolbarButton
              pressed={minLevel === "DEBUG"}
              onClick={() => setMinLevel((prev) => (prev === "DEBUG" ? "INFO" : "DEBUG"))}
            >
              {minLevel === "DEBUG" ? "隐藏调试日志" : "显示调试日志"}
            </RailToolbarButton>
            <RailToolbarButton pressed={autoScroll} onClick={() => setAutoScroll((value) => !value)}>
              {autoScroll ? "暂停滚动" : "自动滚动"}
            </RailToolbarButton>
            <RailToolbarButton onClick={() => onClear?.()}>清空</RailToolbarButton>
          </>
        }
      />
      <div ref={listRef} className="logs-panel__list" role="log" aria-live="polite">
        {visibleEntries.length === 0 ? (
          <PanelEmpty
            variant="inline"
            title={
              entries.length === 0
                ? "暂无日志，开始对话后将显示当前会话日志。"
                : "当前筛选条件下无日志。"
            }
          />
        ) : (
          visibleEntries.map((entry) => <LogLine key={entry.id} entry={entry} />)
        )}
      </div>
    </RailPanelColumn>
  );
}
