import { ClipboardList, Sparkles } from "lucide-react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";

import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import { EvalRunResultView } from "@/features/test/EvalRunResultView";
import { EvalScenarioDetailHeader } from "@/features/test/EvalScenarioDetailHeader";
import { useEvalRun } from "@/features/test/EvalRunProvider";
import { getExplicitFocusedItem } from "@/features/test/evalBatchTypes";
import { TestPanelCollapsibleSection } from "@/features/test/TestPanelCollapsibleSection";
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

export function EvalDomainRunDock({
  error,
  mode,
  emptyTitle,
  emptyDescription,
}: EvalDomainRunDockProps): JSX.Element {
  const { state: evalRunState } = useEvalRun();
  const focusedItem = getExplicitFocusedItem(evalRunState);
  const focusedLive = focusedItem?.live;
  const isExploratoryLive = focusedLive?.tier === "exploratory";
  const isScenarioLive = focusedLive && focusedLive.tier !== "exploratory";
  const scenarioRunning = evalRunState.batchStatus === "running";
  const isRunning = focusedLive?.status === "running";

  const defaultEmpty =
    mode === "exploratory"
      ? {
          title: "等待探索评测",
          description: "填写左侧配置并点击开始测试，详情将显示在这里。",
          icon: Sparkles,
        }
      : {
          title: "场景详情",
          description: "运行后点击左侧场景行，可在此查看进度、断言与评判详情。",
          icon: ClipboardList,
        };

  const emptyIcon = defaultEmpty.icon;
  const title = emptyTitle ?? defaultEmpty.title;
  const description = emptyDescription ?? defaultEmpty.description;

  const showScenarioDetail = mode === "scenario" && isScenarioLive && focusedItem != null;
  const showExploratoryDetail = mode === "exploratory" && isExploratoryLive && focusedItem != null;
  const showEmpty = !error && !showScenarioDetail && !showExploratoryDetail;

  return (
    <div className="eval-domain-run-dock">
      {showScenarioDetail || showExploratoryDetail ? (
        <EvalScenarioDetailHeader
          scenarioId={focusedItem.scenarioId}
          tier={focusedLive.tier}
          status={focusedLive.liveResult.status ?? focusedLive.status}
          judgeOverallPassed={focusedLive.liveResult.judge_overall_passed}
          progressMessage={focusedLive.progressMessage}
          isRunning={isRunning}
        />
      ) : (
        <div className="eval-domain-run-dock__header">
          <h3 className="text-xs font-medium text-foreground">
            {mode === "exploratory" ? "探索详情" : "场景详情"}
          </h3>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            {scenarioRunning ? "点击左侧场景查看详情" : "选择或运行场景后查看详情"}
          </p>
        </div>
      )}

      <div className="eval-domain-run-dock__body space-y-3">
        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-[11px] text-destructive">
            <p className="font-medium">测试失败</p>
            <p className="mt-1 leading-snug">{error}</p>
          </div>
        ) : null}

        {showScenarioDetail ? (
          <>
            <EvalRunProgressView state={focusedLive} variant="compact" />
            <EvalRunResultView omitHeader result={focusedLive.liveResult} />
          </>
        ) : null}

        {showExploratoryDetail ? (
          <>
            <EvalRunProgressView state={focusedLive} variant="compact" />

            {focusedLive.liveResult.summary ? (
              <section className="test-panel-section">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="test-panel-section__eyebrow">综合结论</p>
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
                  <TestPanelCollapsibleSection className="mt-2 border-0 bg-transparent" defaultOpen={false} title="改进建议">
                    <ul className="list-disc space-y-0.5 pl-4 text-[11px] text-muted-foreground">
                      {focusedLive.liveResult.summary.improvement_suggestions?.map((suggestion) => (
                        <li key={suggestion}>{suggestion}</li>
                      ))}
                    </ul>
                  </TestPanelCollapsibleSection>
                ) : null}
              </section>
            ) : null}

            {(focusedLive.liveResult.scores?.length ?? 0) > 0 ? (
              <section className="test-panel-section">
                <h4 className="test-panel-section__title">指标评分</h4>
                <ul className="space-y-1.5">
                  {focusedLive.liveResult.scores?.map((metric) => (
                    <li className="test-panel-card" key={metric.name}>
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[11px] font-medium text-foreground/90">{metric.name}</p>
                        <p className="test-text-score text-[11px]">{formatScore(metric.score)}</p>
                      </div>
                      <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{metric.reason}</p>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {(focusedLive.liveResult.observations?.length ?? 0) > 0 ? (
              <TestPanelCollapsibleSection
                defaultOpen={(focusedLive.liveResult.observations?.length ?? 0) <= 1}
                title={`对话轮次（${focusedLive.liveResult.observations?.length ?? 0}）`}
              >
                <ul className="space-y-1.5">
                  {focusedLive.liveResult.observations?.map((turn) => (
                    <li className="test-panel-card" key={turn.round}>
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <p className="text-[10px] font-medium text-muted-foreground">第 {turn.round} 轮</p>
                        {turn.agent_affect?.emotion ? (
                          <span className="test-status-badge test-status-badge--neutral">
                            {turn.agent_affect.emotion}
                          </span>
                        ) : null}
                      </div>
                      <div className="space-y-1 text-[11px] leading-snug">
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
              </TestPanelCollapsibleSection>
            ) : null}
          </>
        ) : null}

        {showEmpty ? (
          <PanelEmpty variant="compact" icon={emptyIcon} description={description} title={title} />
        ) : null}
      </div>
    </div>
  );
}
