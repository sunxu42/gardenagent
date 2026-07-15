import type { BatchEvalItem } from "@/features/test/evalBatchTypes";
import { isTerminalBatchItemStatus } from "@/features/test/evalBatchTypes";
import { EvalRunStatusIcon, formatEvalItemSummary } from "@/features/test/evalRunItemSummary";
import { labelAssertionStatus } from "@/lib/uiLabels";
import { cn } from "@/lib/utils";

interface EvalScenarioRunInlineProps {
  item: BatchEvalItem;
}

function assertionChipClass(status: string): string {
  if (status === "pass") {
    return "eval-scenario-assertion eval-scenario-assertion--pass";
  }
  if (status === "fail") {
    return "eval-scenario-assertion eval-scenario-assertion--fail";
  }
  if (status === "warn") {
    return "eval-scenario-assertion eval-scenario-assertion--warn";
  }
  return "eval-scenario-assertion eval-scenario-assertion--skip";
}

export function EvalScenarioRunInline({ item }: EvalScenarioRunInlineProps): JSX.Element {
  const assertions = item.live.liveResult.assertions ?? [];
  const summary = formatEvalItemSummary(item);
  const showAssertions =
    assertions.length > 0 &&
    (item.status === "running" || isTerminalBatchItemStatus(item.status));

  return (
    <div className="eval-scenario-run-inline mt-2 border-t border-border/25 pt-2">
      <div className="flex items-start gap-2">
        <EvalRunStatusIcon item={item} />
        <p className="min-w-0 flex-1 text-[10px] leading-snug text-muted-foreground">{summary}</p>
      </div>
      {showAssertions ? (
        <ul className="mt-1.5 flex flex-wrap gap-1" aria-label="断言结果">
          {assertions.map((assertion) => (
            <li key={assertion.name}>
              <span
                className={cn(assertionChipClass(assertion.status))}
                title={assertion.message || undefined}
              >
                {assertion.name}
                <span className="eval-scenario-assertion__status">
                  {labelAssertionStatus(assertion.status)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
