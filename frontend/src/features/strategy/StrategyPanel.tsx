import {
  Activity,
  Brain,
  FileCode2,
  ScrollText,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import type { AffectDebugPanelProps } from "@/features/chat/components/AffectDebugPanel";
import {
  LazyAffectPanel,
  LazyPromptPanel,
  LogsPanel,
  MemoryPanel,
} from "./panels/LazyStrategyPanels";
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
];

export interface StrategyPanelProps extends AffectDebugPanelProps {
  activeTab: StrategyPanelTab;
  onTabChange: (tab: StrategyPanelTab) => void;
}

export function StrategyPanel({
  activeTab,
  onTabChange,
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
      <nav className="strategy-rail-tabs" aria-label="策略分区">
        {TABS.map(({ id, icon: Icon, label }) => {
          const selected = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              className={`strategy-rail-tab cursor-pointer${selected ? " strategy-rail-tab--active" : ""}`}
              aria-current={selected ? "page" : undefined}
              aria-label={label}
              title={label}
              onClick={() => onTabChange(id)}
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span className="strategy-rail-tab__label">{label}</span>
            </button>
          );
        })}
      </nav>

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
            <LogsPanel />
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
      </div>
    </div>
  );
}
