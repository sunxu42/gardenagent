import { FlaskConical, History, LayoutGrid } from "lucide-react";
import { useState } from "react";

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
  const [panelView, setPanelView] = useState<PanelView>("radar");
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const coverage = useCoverageMatrix();
  useCoverageRefreshOnEvalComplete(coverage.reload);

  return (
    <section className="test-panel-root flex h-full min-h-0 flex-col overflow-hidden">
      <header className="affect-rail-header shrink-0">
        <div className="affect-rail-header__row">
          <h2 className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
            <span className="affect-rail-header__icon">
              <FlaskConical className="h-3.5 w-3.5" aria-hidden />
            </span>
            测试
          </h2>
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
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-hidden">
        {activeTab === "overview" ? (
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
        ) : null}

        {activeTab === "history" ? <EvalHistoryView /> : null}
      </div>
    </section>
  );
}
