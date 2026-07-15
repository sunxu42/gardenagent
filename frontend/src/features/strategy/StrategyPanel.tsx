import {
  Activity,
  Brain,
  FileCode2,
  FlaskConical,
  LayoutTemplate,
  ScrollText,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { StrategyRailTabs } from "./StrategyRailTabs";
import type { AffectDebugPanelProps } from "@/features/chat/components/AffectDebugPanel";
import {
  LazyAffectPanel,
  LazyA2UIPanel,
  LazyLogsPanel,
  LazyMemoryPanel,
  LazyPromptPanel,
  LazyTestPanel,
  prefetchStrategyPanel,
} from "./panels/LazyStrategyPanels";
import type { LogEntry } from "@/features/logs/logTypes";
import {
  STRATEGY_TAB_LABELS,
  type StrategyPanelTab,
  type StrategyTabGroup,
} from "./types";
import "./strategy-desktop.css";

interface TabConfig {
  id: StrategyPanelTab;
  icon: LucideIcon;
  label: string;
  group: StrategyTabGroup;
}

const TABS: TabConfig[] = [
  { id: "prompt", icon: FileCode2, label: STRATEGY_TAB_LABELS.prompt, group: "prompt" },
  { id: "memory", icon: Brain, label: STRATEGY_TAB_LABELS.memory, group: "context" },
  { id: "emotion", icon: Activity, label: STRATEGY_TAB_LABELS.emotion, group: "context" },
  { id: "a2ui", icon: LayoutTemplate, label: STRATEGY_TAB_LABELS.a2ui, group: "interaction" },
  { id: "test", icon: FlaskConical, label: STRATEGY_TAB_LABELS.test, group: "devtools" },
  { id: "logs", icon: ScrollText, label: STRATEGY_TAB_LABELS.logs, group: "devtools" },
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
      <StrategyRailTabs
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={onTabChange}
        onTabPrefetch={prefetchStrategyPanel}
      />

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
            <LazyMemoryPanel />
          </div>
        ) : null}
        {visitedTabs.has("a2ui") ? (
          <div
            className={`strategy-rail-pane h-full min-h-0${activeTab === "a2ui" ? "" : " strategy-rail-pane--hidden"}`}
            aria-hidden={activeTab !== "a2ui"}
          >
            <LazyA2UIPanel />
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
