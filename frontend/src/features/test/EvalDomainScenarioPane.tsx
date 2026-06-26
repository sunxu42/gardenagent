import { Play, Square } from "lucide-react";

import { ScenarioPicker } from "@/features/test/ScenarioPicker";

interface EvalDomainScenarioPaneProps {
  domainId: string;
  tier: "smoke" | "judge";
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  disabled: boolean;
  running: boolean;
  onRun: () => void;
  onCancel: () => void;
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
}: EvalDomainScenarioPaneProps): JSX.Element {
  return (
    <div className="eval-domain-pane">
      <ScenarioPicker
        key={`${domainId}-${tier}`}
        disabled={disabled}
        domain={domainId}
        selectedIds={selectedIds}
        tier={tier}
        onChange={onChange}
      />

      <button
        className={`test-action-btn mt-3 shrink-0 ${
          running ? "test-action-btn--cancel" : "test-action-btn--run"
        }`}
        disabled={!running && selectedIds.length === 0}
        type="button"
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
      </button>
    </div>
  );
}
