import { useCallback, useEffect, useState } from "react";

import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailCheckboxField } from "@/components/rail/RailCheckboxField";
import { Button } from "@/components/ui/button";
import type { ScenarioSummary } from "@/features/test/types";
import { listScenarios } from "@/services/eval/scenarioApi";

interface ScenarioPickerProps {
  tier?: "smoke" | "judge";
  domain?: string;
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  disabled?: boolean;
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

export function ScenarioPicker({
  tier,
  domain,
  selectedIds,
  onChange,
  disabled = false,
}: ScenarioPickerProps): JSX.Element {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    listScenarios(tier)
      .then((items) => {
        if (!active) {
          return;
        }
        const filtered = filterScenarios(items, tier, domain);
        setScenarios(filtered);
        onChange(selectedIds.filter((id) => filtered.some((item) => item.id === id)));
      })
      .catch((loadError: unknown) => {
        if (!active) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "加载场景失败");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tier, domain]);

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
          {selectedIds.length > 0 ? `已选 ${selectedIds.length} 项` : "勾选要运行的场景"}
        </p>
      </div>

      {loading ? <PanelLoading label="加载场景…" fill={false} className="py-4" /> : null}

      {error ? <p className="px-1 text-xs text-destructive">{error}</p> : null}

      <ul
        aria-label="要运行的场景"
        className="test-panel-scroll m-0 list-none space-y-1.5 p-0 !px-1 !pb-2 !pt-0"
        role="group"
      >
        {scenarios.map((scenario) => {
          const checked = selectedIds.includes(scenario.id);
          return (
            <li key={scenario.id}>
              <RailCheckboxField
                checked={checked}
                disabled={disabled}
                id={`scenario-${scenario.id}`}
                onCheckedChange={(next) => toggleScenario(scenario.id, next)}
              >
                <span className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-xs font-medium text-foreground/90">{scenario.id}</span>
                  <span className="shrink-0 text-[10px] text-muted-foreground">{scenario.domain}</span>
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
              </RailCheckboxField>
            </li>
          );
        })}
        {!loading && scenarios.length === 0 ? (
          <li className="py-8 text-center text-xs text-muted-foreground">暂无场景</li>
        ) : null}
      </ul>
    </div>
  );
}
