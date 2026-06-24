import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { LogEntry } from "./logTypes";
import { LEVEL_COLORS, MODULE_COLORS, MODULE_SHORT } from "./logColors";
import { labelLogLevel, labelLogModule } from "@/lib/uiLabels";

function formatLogTime(tsMs: number): string {
  const dt = new Date(tsMs);
  if (Number.isNaN(dt.getTime())) {
    return String(tsMs);
  }
  const h = String(dt.getHours()).padStart(2, "0");
  const m = String(dt.getMinutes()).padStart(2, "0");
  const s = String(dt.getSeconds()).padStart(2, "0");
  const ms = String(dt.getMilliseconds()).padStart(3, "0");
  return `${h}:${m}:${s}.${ms}`;
}

function formatExtra(extra: Record<string, unknown>): string {
  try {
    return JSON.stringify(extra, null, 2);
  } catch {
    return String(extra);
  }
}

interface LogLineProps {
  entry: LogEntry;
}

export function LogLine({ entry }: LogLineProps) {
  const [expanded, setExpanded] = useState(false);
  const hasExtra = Boolean(entry.extra && Object.keys(entry.extra).length > 0);
  const isMetrics = entry.module === "METRICS";
  const expandable = hasExtra && (isMetrics || entry.level === "ERROR");

  return (
    <div className="logs-line">
      <div className="logs-line__row">
        <time className="logs-line__time" dateTime={String(entry.tsMs)}>
          {formatLogTime(entry.tsMs)}
        </time>
        <span
          className="logs-line__badge"
          style={{
            color: MODULE_COLORS[entry.module],
            borderColor: `${MODULE_COLORS[entry.module]}55`,
          }}
          title={labelLogModule(entry.module)}
        >
          {MODULE_SHORT[entry.module]}
        </span>
        <span className="logs-line__level" style={{ color: LEVEL_COLORS[entry.level] }}>
          {labelLogLevel(entry.level)}
        </span>
        <span className="logs-line__message">{entry.message}</span>
        {expandable ? (
          <button
            type="button"
            className="logs-line__expand"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            aria-label={expanded ? "收起详情" : "展开详情"}
          >
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        ) : (
          <span className="logs-line__expand-spacer" aria-hidden />
        )}
      </div>
      {expandable && expanded && entry.extra ? (
        <pre className="logs-line__extra">{formatExtra(entry.extra)}</pre>
      ) : null}
    </div>
  );
}
