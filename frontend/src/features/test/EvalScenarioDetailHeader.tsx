import { formatScenarioDisplayName } from "@/features/test/scenarioDisplayName";
import { labelEvalTier, labelRunStatus } from "@/lib/uiLabels";

function statusBadgeClass(status: string): string {
  if (status === "pass" || status === "completed") {
    return "test-status-badge test-status-badge--pass";
  }
  if (status === "fail" || status === "failed") {
    return "test-status-badge test-status-badge--fail";
  }
  if (status === "running") {
    return "test-status-badge test-status-badge--running";
  }
  return "test-status-badge test-status-badge--neutral";
}

interface EvalScenarioDetailHeaderProps {
  scenarioId: string;
  tier?: string | null;
  status?: string | null;
  judgeOverallPassed?: boolean | null;
  progressMessage?: string | null;
  isRunning?: boolean;
}

export function EvalScenarioDetailHeader({
  scenarioId,
  tier,
  status,
  judgeOverallPassed,
  progressMessage,
  isRunning = false,
}: EvalScenarioDetailHeaderProps): JSX.Element {
  const displayName = formatScenarioDisplayName(scenarioId);
  const tierLabel = tier ? labelEvalTier(tier) : null;

  return (
    <header className="eval-scenario-detail-hero">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="eval-scenario-detail-hero__title">{displayName}</h3>
          <p className="eval-scenario-detail-hero__meta">
            {tierLabel}
            {isRunning && progressMessage ? (
              <>
                {tierLabel ? " · " : null}
                <span className="text-foreground/80">{progressMessage}</span>
              </>
            ) : null}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          {isRunning ? (
            <span className={statusBadgeClass("running")}>{labelRunStatus("running")}</span>
          ) : status ? (
            <span className={statusBadgeClass(status)}>{labelRunStatus(status)}</span>
          ) : null}
          {!isRunning && judgeOverallPassed != null ? (
            <span className={statusBadgeClass(judgeOverallPassed ? "pass" : "fail")}>
              评判 {judgeOverallPassed ? "通过" : "未通过"}
            </span>
          ) : null}
        </div>
      </div>
    </header>
  );
}
