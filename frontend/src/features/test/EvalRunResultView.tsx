import { useState } from "react";

import type { EvalRunResponse } from "@/features/test/types";
import {
  formatDurationZh,
  labelAssertionStatus,
  labelRunStatus,
  labelVerdict,
} from "@/lib/uiLabels";

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function statusBadgeClass(status: string): string {
  if (status === "pass") {
    return "test-status-badge test-status-badge--pass";
  }
  if (status === "fail") {
    return "test-status-badge test-status-badge--fail";
  }
  if (status === "running") {
    return "test-status-badge test-status-badge--running";
  }
  return "test-status-badge test-status-badge--neutral";
}

interface EvalRunResultViewProps {
  result: Partial<EvalRunResponse>;
}

export function EvalRunResultView({ result }: EvalRunResultViewProps): JSX.Element | null {
  const hasContent =
    (result.observations?.length ?? 0) > 0 ||
    (result.assertions?.length ?? 0) > 0 ||
    (result.judge?.length ?? 0) > 0 ||
    (result.scores?.length ?? 0) > 0 ||
    Boolean(result.scenario_id);

  if (!hasContent) {
    return null;
  }

  return (
    <div className="space-y-3">
      <section className="rounded-lg border border-border/30 border-l-[3px] border-l-slate-400/45 bg-muted/15 px-3.5 py-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              场景
            </p>
            <p className="mt-0.5 truncate text-[13px] font-medium text-foreground">
              {result.scenario_id}
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {result.status ? (
              <span className={statusBadgeClass(result.status)}>{labelRunStatus(result.status)}</span>
            ) : null}
            {result.judge_overall_passed !== null && result.judge_overall_passed !== undefined ? (
              <span
                className={statusBadgeClass(result.judge_overall_passed ? "pass" : "fail")}
              >
                评判 {result.judge_overall_passed ? "通过" : "未通过"}
              </span>
            ) : null}
          </div>
        </div>
      </section>

      {(result.assertions?.length ?? 0) > 0 ? (
        <section className="rounded-lg border border-border/30 border-l-[3px] border-l-amber-500/50 bg-amber-500/[0.04] px-3.5 py-3">
          <h4 className="mb-2 text-[13px] font-medium text-foreground">基础断言</h4>
          <ul className="space-y-2">
            {result.assertions?.map((assertion) => (
              <li
                className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                key={assertion.name}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{assertion.name}</p>
                  <span className={statusBadgeClass(assertion.status)}>{labelAssertionStatus(assertion.status)}</span>
                </div>
                <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
                  {assertion.message}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {(result.scores?.length ?? 0) > 0 ? (
        <section className="rounded-lg border border-border/30 border-l-[3px] border-l-teal-500/45 bg-teal-500/[0.04] px-3.5 py-3">
          <h4 className="mb-2 text-[13px] font-medium text-foreground">探索评分</h4>
          {result.summary ? (
            <div className="mb-2 rounded-md border border-border/25 bg-background/40 px-2.5 py-2 text-[11px]">
              <p className="font-medium text-foreground">{result.summary.conclusion}</p>
              <p className="mt-1 text-muted-foreground">
                综合 {formatScore(result.summary.overall_score)} · {labelVerdict(result.summary.verdict)}
              </p>
            </div>
          ) : null}
          <ul className="space-y-2">
            {result.scores?.map((metric) => (
              <li
                className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                key={metric.name}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                  <p className="text-[11px] font-semibold text-primary">{formatScore(metric.score)}</p>
                </div>
                <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">{metric.reason}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {(result.judge?.length ?? 0) > 0 ? (
        <section className="rounded-lg border border-border/30 border-l-[3px] border-l-indigo-500/45 bg-indigo-500/[0.04] px-3.5 py-3">
          <h4 className="mb-2 text-[13px] font-medium text-foreground">评判评分</h4>
          <ul className="space-y-2">
            {result.judge?.map((metric) => (
              <li
                className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                key={metric.name}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                  <p className="text-[11px] font-semibold text-primary">{formatScore(metric.score)}</p>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  阈值 {formatScore(metric.threshold)} ·{" "}
                  <span className={metric.passed ? "text-emerald-600" : "text-destructive"}>
                    {metric.passed ? "通过" : "未通过"}
                  </span>
                </p>
                <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">{metric.reason}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {(result.observations?.length ?? 0) > 0 ? (
        <section className="rounded-lg border border-border/30 border-l-[3px] border-l-violet-500/45 bg-violet-500/[0.04] px-3.5 py-3">
          <h4 className="mb-2 text-[13px] font-medium text-foreground">对话轮次</h4>
          <ul className="space-y-2">
            {result.observations?.map((turn) => (
              <ObservationTurnItem key={turn.round} turn={turn} />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function ObservationTurnItem({
  turn,
}: {
  turn: NonNullable<EvalRunResponse["observations"]>[number];
}): JSX.Element {
  const [expanded, setExpanded] = useState(false);
  const hasRawUpdates = (turn.raw_updates?.length ?? 0) > 0;

  return (
    <li className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-medium text-muted-foreground">第 {turn.round} 轮</p>
        {turn.latency_ms !== null && turn.latency_ms !== undefined ? (
          <span className="text-[10px] text-muted-foreground">{formatDurationZh(turn.latency_ms)}</span>
        ) : null}
      </div>
      <div className="mt-1.5 space-y-1.5 text-[11px] leading-snug">
        <p>
          <span className="font-medium text-foreground/80">用户 </span>
          <span className="text-muted-foreground">{turn.user}</span>
        </p>
        <p>
          <span className="font-medium text-foreground/80">助手 </span>
          <span className="text-muted-foreground">{turn.assistant}</span>
        </p>
      </div>
      {hasRawUpdates ? (
        <button
          className="mt-2 cursor-pointer text-[10px] text-primary hover:underline"
          type="button"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "收起原始流" : "展开原始流"}
        </button>
      ) : null}
      {expanded && hasRawUpdates ? (
        <pre className="mt-2 max-h-32 overflow-auto rounded border border-border/20 bg-muted/20 p-2 text-[10px] leading-snug text-muted-foreground">
          {turn.raw_updates?.join("\n")}
        </pre>
      ) : null}
    </li>
  );
}
