import {
  Activity,
  Brain,
  FileCode2,
  FlaskConical,
  ScrollText,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { StrategyRailTabs } from "./StrategyRailTabs";
import type { AffectDebugPanelProps } from "@/features/chat/components/AffectDebugPanel";
import {
  LazyAffectPanel,
  LazyLogsPanel,
  LazyPromptPanel,
  LazyTestPanel,
  MemoryPanel,
} from "./panels/LazyStrategyPanels";
import type { LogEntry } from "@/features/logs/logTypes";
import {
  STRATEGY_TAB_LABELS,
  type StrategyPanelTab,
} from "./types";
import "./strategy-desktop.css";

interface TabConfig {
  id: StrategyPanelTab;
  icon: LucideIcon;
  label: string;
}

const TABS: TabConfig[] = [
  { id: "emotion", icon: Activity, label: STRATEGY_TAB_LABELS.emotion },
  { id: "prompt", icon: FileCode2, label: STRATEGY_TAB_LABELS.prompt },
  { id: "logs", icon: ScrollText, label: STRATEGY_TAB_LABELS.logs },
  { id: "memory", icon: Brain, label: STRATEGY_TAB_LABELS.memory },
  { id: "test", icon: FlaskConical, label: STRATEGY_TAB_LABELS.test },
];

export interface StrategyPanelProps extends AffectDebugPanelProps {
  activeTab: StrategyPanelTab;
  onTabChange: (tab: StrategyPanelTab) => void;
  logEntries?: LogEntry[];
  onClearLogs?: () => void;
}

export function StrategyPanel({
  activeTab,
  onTabChange,
  logEntries = [],
  onClearLogs,
  ...affectProps
}: StrategyPanelProps) {
  const [visitedTabs, setVisitedTabs] = useState<Set<StrategyPanelTab>>(() => new Set([activeTab]));

  useEffect(() => {
    setVisitedTabs((prev) => {
      if (prev.has(activeTab)) {
        return prev;
      }
      const next = new Set(prev);
      next.add(activeTab);
      return next;
    });
  }, [activeTab]);

  return (
    <div
      className="strategy-rail flex h-full min-h-0 max-h-full shrink-0 flex-row overflow-hidden"
      role="complementary"
      aria-label="策略面板"
    >
      <StrategyRailTabs tabs={TABS} activeTab={activeTab} onTabChange={onTabChange} />

      <div className="strategy-rail-content min-h-0 min-w-0 flex-1 overflow-hidden">
        {visitedTabs.has("emotion") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "emotion" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "emotion"}
          >
            <LazyAffectPanel {...affectProps} />
          </div>
        ) : null}
        {visitedTabs.has("prompt") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "prompt" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "prompt"}
          >
            <LazyPromptPanel />
          </div>
        ) : null}
        {visitedTabs.has("logs") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "logs" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "logs"}
          >
            <LazyLogsPanel entries={logEntries} onClear={() => onClearLogs?.()} />
          </div>
        ) : null}
        {visitedTabs.has("memory") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "memory" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "memory"}
          >
            <MemoryPanel />
          </div>
        ) : null}
        {visitedTabs.has("test") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "test" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "test"}
          >
            <LazyTestPanel />
          </div>
        ) : null}
      </div>
    </div>
  );
}
