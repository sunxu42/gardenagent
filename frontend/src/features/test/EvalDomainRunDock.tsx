import { ClipboardList, FlaskConical, Sparkles } from "lucide-react";

import { EvalBatchQueueView } from "@/features/test/EvalBatchQueueView";
import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import { EvalRunResultView } from "@/features/test/EvalRunResultView";
import { useEvalRun } from "@/features/test/EvalRunProvider";
import { getFocusedItem, shouldShowBatchQueue } from "@/features/test/evalBatchTypes";
import { labelVerdict } from "@/lib/uiLabels";

interface EvalDomainRunDockProps {
  error: string | null;
  mode: "scenario" | "exploratory";
  emptyTitle?: string;
  emptyDescription?: string;
}

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function TestEmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof FlaskConical;
  title: string;
  description: string;
}): JSX.Element {
  return (
    <div className="test-empty-state">
      <div className="test-empty-state__icon">
        <Icon className="h-4 w-4" aria-hidden />
      </div>
      <p className="test-empty-state__title">{title}</p>
      <p className="test-empty-state__desc">{description}</p>
    </div>
  );
}

export function EvalDomainRunDock({
  error,
  mode,
  emptyTitle,
  emptyDescription,
}: EvalDomainRunDockProps): JSX.Element {
  const { state: evalRunState, dispatch: dispatchEvalRun } = useEvalRun();
  const focusedItem = getFocusedItem(evalRunState);
  const focusedLive = focusedItem?.live;
  const showBatchQueue = shouldShowBatchQueue(evalRunState);
  const hasScenarioResult = Boolean(focusedLive?.liveResult.scenario_id);
  const isExploratoryLive = focusedLive?.tier === "exploratory";
  const isScenarioLive = focusedLive && focusedLive.tier !== "exploratory";
  const scenarioRunning = evalRunState.batchStatus === "running";

  const defaultEmpty =
    mode === "exploratory"
      ? {
          title: "等待探索评测",
          description: "填写左侧配置并点击开始测试，进度与评分将实时显示在这里。",
          icon: Sparkles,
        }
      : {
          title: "尚未开始评测",
          description: "从左侧勾选场景并点击运行，断言与评判结果会显示在这里。",
          icon: ClipboardList,
        };

  const emptyIcon = defaultEmpty.icon;
  const title = emptyTitle ?? defaultEmpty.title;
  const description = emptyDescription ?? defaultEmpty.description;

  const showEmpty =
    !scenarioRunning &&
    !error &&
    (mode === "exploratory" ? !isExploratoryLive : !hasScenarioResult);

  return (
    <div className="eval-domain-run-dock">
      <div className="eval-domain-run-dock__header">
        <h3 className="text-xs font-medium text-foreground">
          {mode === "exploratory" ? "探索过程" : "运行过程"}
        </h3>
        <p className="mt-0.5 text-[10px] text-muted-foreground">
          {focusedLive?.progressMessage ??
            (scenarioRunning ? "实时推送评测进度" : "运行后在此查看进度与结果")}
        </p>
      </div>

      <div className="eval-domain-run-dock__body space-y-3">
        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-[11px] text-destructive">
            <p className="font-medium">测试失败</p>
            <p className="mt-1 leading-snug">{error}</p>
          </div>
        ) : null}

        {mode === "scenario" && showBatchQueue ? (
          <EvalBatchQueueView
            focusedScenarioId={evalRunState.focusedScenarioId}
            state={evalRunState}
            onFocus={(scenarioId) =>
              dispatchEvalRun({ type: "BATCH_FOCUS", payload: { scenarioId } })
            }
            onToggleExpand={(scenarioId) =>
              dispatchEvalRun({ type: "BATCH_TOGGLE_EXPAND", payload: { scenarioId } })
            }
          />
        ) : null}

        {mode === "scenario" && isScenarioLive ? (
          <>
            <EvalRunProgressView state={focusedLive} />
            <EvalRunResultView result={focusedLive.liveResult} />
          </>
        ) : null}

        {mode === "exploratory" && isExploratoryLive ? (
          <>
            <EvalRunProgressView state={focusedLive} />

            {focusedLive.liveResult.summary ? (
              <section className="rounded-lg border border-border/30 border-l-[3px] border-l-emerald-500/45 bg-emerald-500/[0.04] px-3.5 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      总分
                    </p>
                    <p className="text-xl font-semibold text-foreground">
                      {formatScore(focusedLive.liveResult.summary.overall_score)}
                    </p>
                  </div>
                  <span className="test-status-badge test-status-badge--neutral">
                    {labelVerdict(focusedLive.liveResult.summary.verdict)}
                  </span>
                </div>
                <p className="mt-2 text-[11px] leading-snug text-muted-foreground">
                  {focusedLive.liveResult.summary.conclusion}
                </p>
                {(focusedLive.liveResult.summary.improvement_suggestions?.length ?? 0) > 0 ? (
                  <ul className="mt-2 list-disc space-y-0.5 pl-4 text-[11px] text-muted-foreground">
                    {focusedLive.liveResult.summary.improvement_suggestions?.map((suggestion) => (
                      <li key={suggestion}>{suggestion}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}

            {(focusedLive.liveResult.scores?.length ?? 0) > 0 ? (
              <section className="rounded-lg border border-border/30 border-l-[3px] border-l-indigo-500/45 bg-indigo-500/[0.04] px-3.5 py-3">
                <h4 className="mb-2 text-[13px] font-medium text-foreground">指标评分</h4>
                <ul className="space-y-2">
                  {focusedLive.liveResult.scores?.map((metric) => (
                    <li
                      className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                      key={metric.name}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                        <p className="text-[11px] font-semibold text-primary">
                          {formatScore(metric.score)}
                        </p>
                      </div>
                      <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
                        {metric.reason}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {(focusedLive.liveResult.observations?.length ?? 0) > 0 ? (
              <section className="rounded-lg border border-border/30 border-l-[3px] border-l-violet-500/45 bg-violet-500/[0.04] px-3.5 py-3">
                <h4 className="mb-2 text-[13px] font-medium text-foreground">对话轮次</h4>
                <ul className="space-y-2">
                  {focusedLive.liveResult.observations?.map((turn) => (
                    <li
                      className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                      key={turn.round}
                    >
                      <div className="mb-1.5 flex items-center justify-between gap-2">
                        <p className="text-[10px] font-medium text-muted-foreground">
                          第 {turn.round} 轮
                        </p>
                        {turn.agent_affect?.emotion ? (
                          <span className="test-status-badge test-status-badge--neutral">
                            {turn.agent_affect.emotion}
                          </span>
                        ) : null}
                      </div>
                      <div className="space-y-1.5 text-[11px] leading-snug">
                        <p>
                          <span className="font-medium text-foreground/80">用户 </span>
                          <span className="text-muted-foreground">{turn.user}</span>
                        </p>
                        <p>
                          <span className="font-medium text-foreground/80">助手 </span>
                          <span className="text-muted-foreground">{turn.assistant}</span>
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </>
        ) : null}

        {showEmpty ? (
          <TestEmptyState description={description} icon={emptyIcon} title={title} />
        ) : null}
      </div>
    </div>
  );
}
