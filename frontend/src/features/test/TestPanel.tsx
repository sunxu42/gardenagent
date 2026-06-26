import { FlaskConical, History, LayoutGrid } from "lucide-react";
import { useEffect, useState } from "react";

import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import { RailPanelBody, RailPanelRoot } from "@/components/rail/RailPanelShell";
import { RailTab, RailTabList } from "@/components/rail/RailTabGroup";
import { EvalHistoryView } from "@/features/test/EvalHistoryView";
import { EvalOverviewView } from "@/features/test/EvalOverviewView";
import { useCoverageMatrix } from "@/features/test/useCoverageMatrix";
import { useCoverageRefreshOnEvalComplete } from "@/features/test/useCoverageRefreshOnEvalComplete";
import type { PanelTab, PanelView } from "@/features/test/types";

import "./test-panel.css";

const PANEL_TABS = [
  { id: "overview" as const, label: "总览", icon: LayoutGrid },
  { id: "history" as const, label: "运行历史", icon: History },
];

export function TestPanel(): JSX.Element {
  const [activeTab, setActiveTab] = useState<PanelTab>("overview");
  const [visitedTabs, setVisitedTabs] = useState<Set<PanelTab>>(() => new Set([activeTab]));
  const [panelView, setPanelView] = useState<PanelView>("radar");
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const coverage = useCoverageMatrix();
  useCoverageRefreshOnEvalComplete(coverage.reload);

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
    <RailPanelRoot className="test-panel-root" aria-label="评测">
      <RailPanelHeader
        icon={FlaskConical}
        title="测试"
        actions={
          <RailTabList aria-label="评测类型">
            {PANEL_TABS.map((tab) => (
              <RailTab
                key={tab.id}
                selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </RailTab>
            ))}
          </RailTabList>
        }
      />

      <RailPanelBody>
        {visitedTabs.has("overview") ? (
          <div
            className={`test-panel-pane h-full min-h-0${activeTab === "overview" ? "" : " test-panel-pane--hidden"}`}
            aria-hidden={activeTab !== "overview"}
          >
            <EvalOverviewView
              panelView={panelView}
              selectedDomainId={selectedDomainId}
              coverage={coverage}
              onBackToRadar={() => {
                setPanelView("radar");
              }}
              onEnterDomain={(domainId) => {
                setSelectedDomainId(domainId);
                setPanelView({ kind: "domain", domainId });
              }}
              onSelectDomain={setSelectedDomainId}
            />
          </div>
        ) : null}

        {visitedTabs.has("history") ? (
          <div
            className={`test-panel-pane h-full min-h-0${activeTab === "history" ? "" : " test-panel-pane--hidden"}`}
            aria-hidden={activeTab !== "history"}
          >
            <EvalHistoryView />
          </div>
        ) : null}
      </RailPanelBody>
    </RailPanelRoot>
  );
}
