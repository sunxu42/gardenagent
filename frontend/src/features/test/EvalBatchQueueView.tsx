import {
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";

import type { BatchEvalItem } from "@/features/test/evalBatchTypes";
import {
  countFinishedItems,
  isTerminalBatchItemStatus,
} from "@/features/test/evalBatchTypes";
import type { EvalRunRootState } from "@/features/test/evalBatchTypes";
import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import { EvalRunResultView } from "@/features/test/EvalRunResultView";

function formatItemSummary(item: BatchEvalItem): string {
  if (item.status === "pending") {
    return "等待中";
  }
  if (item.status === "running") {
    if (item.live.agentProgress) {
      return `对话 ${item.live.agentProgress.current}/${item.live.agentProgress.total}`;
    }
    return item.live.progressMessage ?? "运行中";
  }
  if (item.status === "cancelled") {
    return "已取消";
  }
  const assertions = item.live.liveResult.assertions ?? [];
  const passed = assertions.filter((entry) => entry.status === "pass").length;
  const judgePassed = item.live.liveResult.judge_overall_passed;
  if (item.status === "failed") {
    return item.live.error ?? `断言 ${passed}/${assertions.length}`;
  }
  const judgeLabel =
    judgePassed == null ? "" : judgePassed ? " · 评判通过" : " · 评判未通过";
  return `断言 ${passed}/${assertions.length}${judgeLabel}`;
}

function StatusIcon({ item }: { item: BatchEvalItem }): JSX.Element {
  if (item.status === "running") {
    return (
      <Loader2
        className="h-3.5 w-3.5 shrink-0 animate-spin text-primary motion-reduce:animate-none"
        aria-hidden
      />
    );
  }
  if (item.status === "completed") {
    return <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden />;
  }
  if (item.status === "failed") {
    return <XCircle className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden />;
  }
  if (item.status === "cancelled") {
    return <Ban className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />;
  }
  return <Circle className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" aria-hidden />;
}

function rowClassName(item: BatchEvalItem, focused: boolean): string {
  const base =
    "w-full cursor-pointer rounded-md border px-2.5 py-2 text-left transition-colors duration-200";
  if (focused) {
    return `${base} border-rail-border-active/60 bg-rail-list-active`;
  }
  if (item.status === "completed") {
    return `${base} border-transparent bg-emerald-500/[0.04] hover:bg-emerald-500/[0.07]`;
  }
  if (item.status === "failed") {
    return `${base} border-transparent bg-destructive/5 hover:bg-destructive/10`;
  }
  if (item.status === "running") {
    return `${base} border-transparent border-l-2 border-l-sky-500/45 bg-rail-list hover:bg-rail-list-hover`;
  }
  return `${base} border-rail-border bg-rail-list hover:bg-rail-list-hover`;
}

interface EvalBatchQueueViewProps {
  state: EvalRunRootState;
  focusedScenarioId: string | null;
  onFocus: (scenarioId: string) => void;
  onToggleExpand: (scenarioId: string) => void;
}

export function EvalBatchQueueView({
  state,
  focusedScenarioId,
  onFocus,
  onToggleExpand,
}: EvalBatchQueueViewProps): JSX.Element {
  const finished = countFinishedItems(state);

  return (
    <section className="space-y-3">
      <div className="rounded-lg border border-border/30 bg-muted/15 px-3.5 py-3">
        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          批次进度 {finished}/{state.items.length}
        </p>
        <ul className="mt-2 space-y-1.5">
          {state.items.map((item) => {
            const focused = item.scenarioId === focusedScenarioId;
            const terminal = isTerminalBatchItemStatus(item.status);
            return (
              <li key={item.scenarioId}>
                <div className={rowClassName(item, focused)}>
                  <button
                    className="flex w-full items-start gap-2"
                    type="button"
                    onClick={() => onFocus(item.scenarioId)}
                  >
                    <StatusIcon item={item} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[11px] font-medium text-foreground/90">
                        {item.scenarioId}
                      </span>
                      <span className="mt-0.5 block text-[10px] text-muted-foreground">
                        {formatItemSummary(item)}
                      </span>
                    </span>
                  </button>
                  {terminal ? (
                    <button
                      aria-expanded={item.expanded}
                      className="mt-1.5 flex cursor-pointer items-center gap-1 text-[10px] text-muted-foreground transition-colors duration-200 hover:text-foreground"
                      type="button"
                      onClick={() => onToggleExpand(item.scenarioId)}
                    >
                      {item.expanded ? (
                        <ChevronDown className="h-3 w-3" aria-hidden />
                      ) : (
                        <ChevronRight className="h-3 w-3" aria-hidden />
                      )}
                      {item.expanded ? "收起详情" : "展开详情"}
                    </button>
                  ) : null}
                  {terminal && item.expanded ? (
                    <div className="mt-2 space-y-2 border-t border-border/20 pt-2">
                      <EvalRunProgressView state={item.live} />
                      <EvalRunResultView result={item.live.liveResult} />
                    </div>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
