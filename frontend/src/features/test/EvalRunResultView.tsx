import { useState } from "react";

import { Button } from "@/components/ui/button";
import { TestPanelCollapsibleSection } from "@/features/test/TestPanelCollapsibleSection";
import type { EvalRunResponse } from "@/features/test/types";
import {
  formatDurationZh,
  labelAssertionStatus,
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
  /** 场景摘要已在父级头部展示时设为 true */
  omitHeader?: boolean;
}

export function EvalRunResultView({
  result,
  omitHeader = false,
}: EvalRunResultViewProps): JSX.Element | null {
  const hasAssertions = (result.assertions?.length ?? 0) > 0;
  const hasJudge = (result.judge?.length ?? 0) > 0;
  const hasScores = (result.scores?.length ?? 0) > 0;
  const hasObservations = (result.observations?.length ?? 0) > 0;
  const hasHeader = !omitHeader && Boolean(result.scenario_id);

  const hasContent = hasAssertions || hasJudge || hasScores || hasObservations || hasHeader;

  if (!hasContent) {
    return null;
  }

  return (
    <div className="space-y-3">
      {hasHeader ? (
        <section className="test-panel-section">
          <p className="test-panel-section__eyebrow">场景</p>
          <p className="mt-0.5 truncate text-[13px] font-medium text-foreground">{result.scenario_id}</p>
        </section>
      ) : null}

      {hasAssertions ? (
        <section className="test-panel-section">
          <h4 className="test-panel-section__title">基础断言</h4>
          <ul className="space-y-1.5">
            {result.assertions?.map((assertion) => (
              <li className="test-panel-card" key={assertion.name}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{assertion.name}</p>
                  <span className={statusBadgeClass(assertion.status)}>
                    {labelAssertionStatus(assertion.status)}
                  </span>
                </div>
                {assertion.message ? (
                  <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{assertion.message}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {hasJudge ? (
        <section className="test-panel-section">
          <h4 className="test-panel-section__title">评判评分</h4>
          <ul className="space-y-1.5">
            {result.judge?.map((metric) => (
              <li className="test-panel-card" key={metric.name}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                  <div className="flex items-center gap-1.5">
                    <p className="test-text-score text-[11px]">{formatScore(metric.score)}</p>
                    <span className={statusBadgeClass(metric.passed ? "pass" : "fail")}>
                      {metric.passed ? "通过" : "未通过"}
                    </span>
                  </div>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  阈值 {formatScore(metric.threshold)}
                </p>
                {metric.reason ? (
                  <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{metric.reason}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {hasScores ? (
        <section className="test-panel-section">
          <h4 className="test-panel-section__title">探索评分</h4>
          {result.summary ? (
            <div className="test-panel-card mb-2 text-[11px]">
              <p className="font-medium text-foreground">{result.summary.conclusion}</p>
              <p className="mt-1 text-muted-foreground">
                综合 {formatScore(result.summary.overall_score)} · {labelVerdict(result.summary.verdict)}
              </p>
            </div>
          ) : null}
          <ul className="space-y-1.5">
            {result.scores?.map((metric) => (
              <li className="test-panel-card" key={metric.name}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                  <p className="test-text-score text-[11px]">{formatScore(metric.score)}</p>
                </div>
                {metric.reason ? (
                  <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{metric.reason}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {hasObservations ? (
        <TestPanelCollapsibleSection
          defaultOpen={(result.observations?.length ?? 0) <= 1}
          title={`对话轮次（${result.observations?.length ?? 0}）`}
        >
          <ul className="space-y-1.5">
            {result.observations?.map((turn) => (
              <ObservationTurnItem key={turn.round} turn={turn} />
            ))}
          </ul>
        </TestPanelCollapsibleSection>
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
    <li className="test-panel-card">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-medium text-muted-foreground">第 {turn.round} 轮</p>
        {turn.latency_ms != null ? (
          <span className="text-[10px] text-muted-foreground">{formatDurationZh(turn.latency_ms)}</span>
        ) : null}
      </div>
      <div className="mt-1.5 space-y-1 text-[11px] leading-snug">
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
        <Button
          type="button"
          variant="link"
          className="test-link mt-2 h-auto p-0 text-[10px]"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "收起原始流" : "展开原始流"}
        </Button>
      ) : null}
      {expanded && hasRawUpdates ? (
        <pre className="mt-2 max-h-32 overflow-auto rounded border border-border/20 bg-muted/20 p-2 text-[10px] leading-snug text-muted-foreground">
          {turn.raw_updates?.join("\n")}
        </pre>
      ) : null}
    </li>
  );
}
