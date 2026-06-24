import { Check, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import type { ScenarioSummary } from "@/features/test/types";
import { listScenarios } from "@/services/eval/scenarioApi";

interface ScenarioPickerProps {
  tier?: "smoke" | "judge";
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  disabled?: boolean;
}

export function ScenarioPicker({
  tier,
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
        setScenarios(items);
        onChange(selectedIds.filter((id) => items.some((item) => item.id === id)));
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
  }, [tier]);

  const toggleScenario = useCallback(
    (scenarioId: string): void => {
      if (disabled) {
        return;
      }
      if (selectedIds.includes(scenarioId)) {
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
        <button
          aria-label={allSelected ? "清空已选场景" : "全选当前列表"}
          className="cursor-pointer text-[10px] text-muted-foreground transition-colors duration-200 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled || scenarios.length === 0}
          type="button"
          onClick={toggleSelectAll}
        >
          {allSelected ? "清空" : "全选"}
        </button>
        <p className="text-[11px] font-medium text-muted-foreground">
          {selectedIds.length > 0 ? `已选 ${selectedIds.length} 项` : "勾选要运行的场景"}
        </p>
      </div>

      {loading ? (
        <p className="flex items-center gap-1.5 px-1 py-6 text-[11px] text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden />
          加载场景…
        </p>
      ) : null}

      {error ? <p className="px-1 text-[11px] text-destructive">{error}</p> : null}

      <ul className="test-panel-scroll space-y-1.5 !px-1 !pb-2 !pt-0">
        {scenarios.map((scenario) => {
          const checked = selectedIds.includes(scenario.id);
          return (
            <li key={scenario.id}>
              <button
                aria-pressed={checked}
                className={`w-full cursor-pointer rounded-md border px-3 py-2.5 text-left transition-colors duration-200 ${
                  checked
                    ? "border-border bg-muted/35"
                    : "border-transparent bg-transparent hover:bg-muted/25"
                } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
                disabled={disabled}
                type="button"
                onClick={() => toggleScenario(scenario.id)}
              >
                <div className="flex gap-2.5">
                  <span
                    className={`mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border transition-colors duration-200 ${
                      checked
                        ? "border-primary/50 bg-primary/15 text-primary"
                        : "border-border/60 bg-transparent"
                    }`}
                    aria-hidden
                  >
                    {checked ? <Check className="h-2.5 w-2.5" strokeWidth={3} /> : null}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className="truncate text-xs font-medium text-foreground/90">
                        {scenario.id}
                      </span>
                      <span className="shrink-0 text-[10px] text-muted-foreground">
                        {scenario.domain}
                      </span>
                    </span>
                    <span className="mt-1 block line-clamp-2 text-[11px] leading-snug text-muted-foreground">
                      {scenario.description}
                    </span>
                  </span>
                </div>
              </button>
            </li>
          );
        })}
        {!loading && scenarios.length === 0 ? (
          <li className="py-8 text-center text-[11px] text-muted-foreground">暂无场景</li>
        ) : null}
      </ul>
    </div>
  );
}
