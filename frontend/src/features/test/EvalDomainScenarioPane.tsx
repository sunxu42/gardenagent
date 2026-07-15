import { Play, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { BatchEvalItem } from "@/features/test/evalBatchTypes";
import { ScenarioPicker } from "@/features/test/ScenarioPicker";
import { cn } from "@/lib/utils";

interface EvalDomainScenarioPaneProps {
  domainId: string;
  tier: "smoke" | "judge";
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  disabled: boolean;
  running: boolean;
  onRun: () => void;
  onCancel: () => void;
  runItems?: BatchEvalItem[];
  focusedScenarioId?: string | null;
  onFocusScenario?: (scenarioId: string) => void;
}

export function EvalDomainScenarioPane({
  domainId,
  tier,
  selectedIds,
  onChange,
  disabled,
  running,
  onRun,
  onCancel,
  runItems,
  focusedScenarioId,
  onFocusScenario,
}: EvalDomainScenarioPaneProps): JSX.Element {
  return (
    <div className="eval-domain-pane">
      <ScenarioPicker
        key={`${domainId}-${tier}`}
        disabled={disabled}
        domain={domainId}
        focusedScenarioId={focusedScenarioId}
        runItems={runItems}
        selectedIds={selectedIds}
        tier={tier}
        onChange={onChange}
        onFocusScenario={onFocusScenario}
      />

      <Button
        type="button"
        variant={running ? "secondary" : "default"}
        disabled={!running && selectedIds.length === 0}
        className={cn(
          "test-action-btn mt-3 h-auto w-full shrink-0",
          running ? "test-action-btn--cancel" : "test-action-btn--run",
        )}
        onClick={running ? onCancel : onRun}
      >
        <span className="inline-flex items-center justify-center gap-1.5">
          {running ? (
            <Square className="h-3 w-3" aria-hidden />
          ) : (
            <Play className="h-3 w-3" aria-hidden />
          )}
          {running
            ? "取消测试"
            : selectedIds.length > 1
              ? `运行 ${selectedIds.length} 个场景`
              : "运行场景"}
        </span>
      </Button>
    </div>
  );
}
