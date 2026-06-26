import { History } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";
import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailChipButton } from "@/components/rail/RailTabGroup";
import { RailListbox, RailListboxOption } from "@/components/rail/RailListbox";

import { EvalRunHistoryTimeline } from "@/features/test/EvalRunHistoryTimeline";
import { EvalRunResultView } from "@/features/test/EvalRunResultView";
import { EvalRunTelemetryView } from "@/features/test/EvalRunTelemetryView";
import { useEvalRun } from "@/features/test/EvalRunProvider";
import { getFocusedItem } from "@/features/test/evalBatchTypes";
import {
  buildScenarioDomainMap,
  filterHistoryItems,
} from "@/features/test/evalHistoryFilters";
import { getErrorMessage } from "@/features/test/evalFormConstants";
import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import {
  RailDetailPane,
  RailListPane,
  RailPanelScroll,
  RailSidebarGroup,
} from "@/components/rail/RailPanelShell";
import type { EvalRunSummary, HistoryDomainFilter, HistoryTierFilter } from "@/features/test/types";
import { formatDurationZh, labelEvalTier, labelRunStatus } from "@/lib/uiLabels";
import { getEvalRun, listEvalRuns, listScenarios } from "@/services/eval/scenarioApi";

const DOMAIN_FILTERS: Array<{ id: HistoryDomainFilter; label: string }> = [
  { id: "all", label: "全部域" },
  { id: "emotion", label: "情感支持" },
  { id: "safety", label: "安全边界" },
  { id: "persona", label: "人设一致" },
  { id: "relationship", label: "关系演化" },
  { id: "memory", label: "记忆" },
  { id: "tools", label: "工具与任务" },
  { id: "dialogue", label: "对话连贯" },
  { id: "transport", label: "传输与性能" },
];

function historyItemTitle(item: EvalRunSummary): string {
  if (item.mode === "exploratory" || item.tier === "exploratory") {
    return "情绪探索";
  }
  return item.scenario_id;
}

export function EvalHistoryView(): JSX.Element {
  const { state: evalRunState, dispatch: dispatchEvalRun } = useEvalRun();
  const [historyItems, setHistoryItems] = useState<EvalRunSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyTierFilter, setHistoryTierFilter] = useState<HistoryTierFilter>("all");
  const [historyDomainFilter, setHistoryDomainFilter] = useState<HistoryDomainFilter>("all");
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [domainMap, setDomainMap] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    let active = true;
    listScenarios()
      .then((scenarios) => {
        if (active) {
          setDomainMap(buildScenarioDomainMap(scenarios));
        }
      })
      .catch(() => {
        if (active) {
          setDomainMap(new Map());
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setHistoryLoading(true);
    const tier = historyTierFilter === "all" ? undefined : historyTierFilter;
    listEvalRuns(tier)
      .then((items) => {
        if (active) {
          setHistoryItems(items);
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(getErrorMessage(loadError));
        }
      })
      .finally(() => {
        if (active) {
          setHistoryLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [historyTierFilter]);

  const filteredItems = useMemo(
    () => filterHistoryItems(historyItems, historyTierFilter, historyDomainFilter, domainMap),
    [domainMap, historyDomainFilter, historyItems, historyTierFilter],
  );

  const handleHistorySelect = async (runId: string): Promise<void> => {
    setSelectedHistoryId(runId);
    setError(null);
    try {
      const result = await getEvalRun(runId);
      dispatchEvalRun({ type: "LOAD_RESULT", payload: result });
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  const focusedLive = getFocusedItem(evalRunState)?.live;
  const historyDetail = selectedHistoryId ? focusedLive?.liveResult : undefined;
  const detailError = error ?? focusedLive?.error;

  return (
    <RailSidebarGroup>
      <RailListPane>
        <RailPanelHeader
          level={3}
          icon={History}
          subtitle="评测运行记录持久化存储"
          title="历史列表"
        />

        <div className="border-b border-border/25 bg-muted/10 px-2 py-2 space-y-2">
          <div className="flex flex-wrap gap-1">
            {(["all", "smoke", "judge", "exploratory"] as const).map((tier) => (
              <RailChipButton
                key={tier}
                selected={historyTierFilter === tier}
                onClick={() => setHistoryTierFilter(tier)}
              >
                {labelEvalTier(tier)}
              </RailChipButton>
            ))}
          </div>

          <div className="flex flex-wrap gap-1">
            {DOMAIN_FILTERS.map((filter) => (
              <RailChipButton
                key={filter.id}
                selected={historyDomainFilter === filter.id}
                onClick={() => setHistoryDomainFilter(filter.id)}
              >
                {filter.label}
              </RailChipButton>
            ))}
          </div>
        </div>

        {historyLoading ? (
          <RailPanelScroll padded className="py-4">
            <PanelLoading label="加载历史…" fill={false} />
          </RailPanelScroll>
        ) : filteredItems.length === 0 ? (
          <RailPanelScroll padded>
            <PanelEmpty
              variant="compact"
              icon={History}
              description="运行场景回归或情绪探索后，记录会出现在这里。"
              title="暂无历史记录"
            />
          </RailPanelScroll>
        ) : (
          <RailListbox aria-label="运行历史" className="rail-panel-scroll rail-panel-scroll--padded">
            {filteredItems.map((item) => (
              <RailListboxOption
                key={item.run_id}
                selected={selectedHistoryId === item.run_id}
                onSelect={() => void handleHistorySelect(item.run_id)}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <p className="truncate text-xs font-medium text-foreground/90">
                    {historyItemTitle(item)}
                  </p>
                  <span className="shrink-0 text-[10px] text-muted-foreground">
                    {labelEvalTier(item.tier)}
                  </span>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {labelRunStatus(item.status)}
                  {item.duration_ms ? ` · ${formatDurationZh(item.duration_ms)}` : ""}
                  {item.finished_at ? ` · ${item.finished_at.slice(0, 19)}` : ""}
                </p>
              </RailListboxOption>
            ))}
          </RailListbox>
        )}
      </RailListPane>

      <RailDetailPane>
        <RailPanelHeader level={3} icon={History} subtitle="选中记录查看详情" title="历史详情" />

        <RailPanelScroll padded className="space-y-3">
          {detailError ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-xs text-destructive">
              <p className="font-medium">加载失败</p>
              <p className="mt-1 leading-snug">{detailError}</p>
            </div>
          ) : null}

          {historyDetail ? (
            <>
              <EvalRunTelemetryView result={historyDetail} />
              <EvalRunHistoryTimeline
                events={historyDetail.events}
                scenarioId={historyDetail.scenario_id}
                status={historyDetail.status}
                tier={historyDetail.tier}
              />
              <EvalRunResultView result={historyDetail} />
            </>
          ) : null}

          {!detailError && !historyDetail ? (
            <PanelEmpty
              variant="compact"
              icon={History}
              description="从左侧选择一条运行记录，完整评测结果将显示在这里。"
              title="未选择记录"
            />
          ) : null}
        </RailPanelScroll>
      </RailDetailPane>
    </RailSidebarGroup>
  );
}
