import { useCallback, useEffect, useMemo, useRef } from "react";

import { PanelLoading } from "@/components/panel/PanelLoading";
import { SyncStatusBadge } from "@/components/panel/SyncStatusBadge";
import { railCheckboxRowClass } from "@/components/rail/railButtonStyles";
import { RailPanelScroll } from "@/components/rail/RailPanelShell";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { EvalScenarioRunInline } from "@/features/test/EvalScenarioRunInline";
import type { BatchEvalItem } from "@/features/test/evalBatchTypes";
import { isTerminalBatchItemStatus } from "@/features/test/evalBatchTypes";
import { formatScenarioDisplayName } from "@/features/test/scenarioDisplayName";
import type { ScenarioSummary } from "@/features/test/types";
import { cn } from "@/lib/utils";
import { scenarioCacheKey } from "@/shared/cache/cacheKeys";
import { useStaleCache } from "@/shared/cache/useStaleCache";
import { listScenarios } from "@/services/eval/scenarioApi";

interface ScenarioPickerProps {
  tier?: "smoke" | "judge";
  domain?: string;
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  disabled?: boolean;
  runItems?: BatchEvalItem[];
  focusedScenarioId?: string | null;
  onFocusScenario?: (scenarioId: string) => void;
}

function filterScenarios(
  items: ScenarioSummary[],
  tier?: "smoke" | "judge",
  domain?: string,
): ScenarioSummary[] {
  return items.filter((scenario) => {
    if (tier && scenario.tier !== tier) {
      return false;
    }
    if (domain && scenario.domain !== domain) {
      return false;
    }
    return true;
  });
}

function scenarioRowClassName(
  checked: boolean,
  runItem: BatchEvalItem | undefined,
  focused: boolean,
): string {
  return cn(
    railCheckboxRowClass(checked),
    "eval-scenario-row overflow-hidden",
    checked && "eval-scenario-row--selected",
    focused && "eval-scenario-row--focused",
    runItem?.status === "running" && "eval-scenario-row--running",
    runItem?.status === "completed" && "eval-scenario-row--completed",
    runItem?.status === "failed" && "eval-scenario-row--failed",
    runItem?.status === "cancelled" && "eval-scenario-row--cancelled",
  );
}

export function ScenarioPicker({
  tier,
  domain,
  selectedIds,
  onChange,
  disabled = false,
  runItems = [],
  focusedScenarioId = null,
  onFocusScenario,
}: ScenarioPickerProps): JSX.Element {
  const cacheKey = scenarioCacheKey(tier);
  const {
    data: rawScenarios,
    isInitialLoading,
    isSyncing,
    syncFailed,
    error,
  } = useStaleCache(cacheKey, ({ signal }) => listScenarios(tier, signal));

  const scenarios = useMemo(
    () => filterScenarios(rawScenarios ?? [], tier, domain),
    [rawScenarios, tier, domain],
  );

  const runItemByScenarioId = useMemo(() => {
    const map = new Map<string, BatchEvalItem>();
    for (const item of runItems) {
      map.set(item.scenarioId, item);
    }
    return map;
  }, [runItems]);

  const runningScenarioId = useMemo(
    () => runItems.find((item) => item.status === "running")?.scenarioId ?? null,
    [runItems],
  );

  const rowRefs = useRef(new Map<string, HTMLLIElement>());

  useEffect(() => {
    if (!runningScenarioId) {
      return;
    }
    const row = rowRefs.current.get(runningScenarioId);
    if (!row) {
      return;
    }
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    row.scrollIntoView({ block: "nearest", behavior: prefersReduced ? "auto" : "smooth" });
  }, [runningScenarioId]);

  const batchProgress =
    runItems.length > 1
      ? {
          finished: runItems.filter((item) => isTerminalBatchItemStatus(item.status)).length,
          total: runItems.length,
        }
      : null;

  useEffect(() => {
    if (isInitialLoading) {
      return;
    }
    const validIds = selectedIds.filter((id) => scenarios.some((item) => item.id === id));
    if (validIds.length !== selectedIds.length) {
      onChange(validIds);
    }
  }, [isInitialLoading, onChange, scenarios, selectedIds]);

  const toggleScenario = useCallback(
    (scenarioId: string, checked: boolean): void => {
      if (disabled) {
        return;
      }
      if (!checked) {
        onChange(selectedIds.filter((id) => id !== scenarioId));
        return;
      }
      onChange([...selectedIds, scenarioId]);
    },
    [disabled, onChange, selectedIds],
  );

  const allSelected = scenarios.length > 0 && selectedIds.length === scenarios.length;

  const toggleSelectAll = (): void => {
    if (disabled) {
      return;
    }
    if (allSelected) {
      onChange([]);
      return;
    }
    onChange(scenarios.map((item) => item.id));
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-2 flex items-center justify-between gap-2 px-1">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-label={allSelected ? "清空已选场景" : "全选当前列表"}
          className="h-auto px-0 py-0 text-[10px] text-muted-foreground hover:bg-transparent hover:text-foreground"
          disabled={disabled || scenarios.length === 0}
          onClick={toggleSelectAll}
        >
          {allSelected ? "清空" : "全选"}
        </Button>
        <p className="text-xs font-medium text-muted-foreground">
          {batchProgress
            ? `批次 ${batchProgress.finished}/${batchProgress.total}`
            : selectedIds.length > 0
              ? `已选 ${selectedIds.length} 项`
              : "勾选要运行的场景"}
        </p>
      </div>

      {isInitialLoading ? <PanelLoading label="加载场景…" fill={false} className="py-4" /> : null}

      {!isInitialLoading && (isSyncing || syncFailed) ? (
        <div className="mb-2 px-1">
          <SyncStatusBadge syncing={isSyncing} syncFailed={syncFailed} />
        </div>
      ) : null}

      {error ? <p className="px-1 text-xs text-destructive">{error}</p> : null}

      <RailPanelScroll padded className="!px-1 !pb-2 !pt-0">
        <ul aria-label="要运行的场景" className="m-0 list-none space-y-1.5 p-0" role="group">
          {scenarios.map((scenario) => {
            const checked = selectedIds.includes(scenario.id);
            const runItem = runItemByScenarioId.get(scenario.id);
            const focused = focusedScenarioId === scenario.id;
            const canOpenDetail = Boolean(runItem && onFocusScenario);
            const detailReady =
              runItem != null &&
              (runItem.status === "running" || isTerminalBatchItemStatus(runItem.status));

            const displayName = formatScenarioDisplayName(scenario.id);

            return (
              <li
                key={scenario.id}
                ref={(element) => {
                  if (element) {
                    rowRefs.current.set(scenario.id, element);
                  } else {
                    rowRefs.current.delete(scenario.id);
                  }
                }}
                className={scenarioRowClassName(checked, runItem, focused)}
              >
                <div className="flex items-start gap-2 px-3 py-2.5">
                  <Checkbox
                    id={`scenario-${scenario.id}`}
                    checked={checked}
                    disabled={disabled}
                    onCheckedChange={(next) => toggleScenario(scenario.id, next === true)}
                    onClick={(event) => event.stopPropagation()}
                    className={cn(
                      "mt-0.5 h-3.5 w-3.5 shrink-0 rounded border shadow-none",
                      checked
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-rail-pick-border bg-rail-pick-check data-[state=checked]:bg-primary",
                      "[&_svg]:h-2.5 [&_svg]:w-2.5",
                      disabled && "cursor-not-allowed opacity-60",
                    )}
                  />

                  <Button
                    type="button"
                    variant="ghost"
                    className={cn(
                      "h-auto min-w-0 flex-1 justify-start rounded-none p-0 text-left font-normal shadow-none hover:bg-transparent",
                      canOpenDetail ? "cursor-pointer" : "cursor-default",
                    )}
                    disabled={!canOpenDetail}
                    aria-pressed={focused}
                    aria-label={
                      detailReady
                        ? `查看 ${displayName} 详情`
                        : `${displayName}${runItem ? `，${runItem.status}` : ""}`
                    }
                    onClick={() => {
                      if (canOpenDetail) {
                        onFocusScenario?.(scenario.id);
                      }
                    }}
                  >
                    <span className="flex items-baseline justify-between gap-2">
                      <span className="truncate text-xs font-medium text-foreground/90">
                        {displayName}
                      </span>
                      <span className="shrink-0 text-[10px] text-muted-foreground">
                        {scenario.domain}
                      </span>
                    </span>
                    <span className="mt-1 block line-clamp-2 text-xs leading-snug text-muted-foreground">
                      {scenario.description}
                    </span>
                    {scenario.tags && scenario.tags.length > 0 ? (
                      <span className="mt-1.5 flex flex-wrap gap-1">
                        {scenario.tags.map((tag) => (
                          <span
                            key={tag}
                            className="test-scenario-tag rounded px-1.5 py-0.5 text-[9px] text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </span>
                    ) : null}
                    {runItem ? <EvalScenarioRunInline item={runItem} /> : null}
                  </Button>
                </div>
              </li>
            );
          })}
          {!isInitialLoading && scenarios.length === 0 ? (
            <li className="py-8 text-center text-xs text-muted-foreground">暂无场景</li>
          ) : null}
        </ul>
      </RailPanelScroll>
    </div>
  );
}
