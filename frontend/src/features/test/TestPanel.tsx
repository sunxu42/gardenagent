import {
  ClipboardList,
  FlaskConical,
  History,
  Loader2,
  Play,
  Sparkles,
  Square,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { EvalBatchQueueView } from "@/features/test/EvalBatchQueueView";
import { EvalRunHistoryTimeline } from "@/features/test/EvalRunHistoryTimeline";
import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import { EvalRunResultView } from "@/features/test/EvalRunResultView";
import { EvalRunTelemetryView } from "@/features/test/EvalRunTelemetryView";
import { useEvalRun } from "@/features/test/EvalRunProvider";
import {
  getFocusedItem,
  getNextPendingItem,
  getRunningItem,
  shouldShowBatchQueue,
} from "@/features/test/evalBatchTypes";
import { ScenarioPicker } from "@/features/test/ScenarioPicker";
import { TestRailHeader } from "@/features/test/TestRailHeader";
import type {
  EmotionEvalRequest,
  EvalRunSummary,
  InitialMood,
} from "@/features/test/types";
import { getOrCreateUserId } from "@/lib/userId";
import { startExploratoryEvalAsync } from "@/services/eval/evalApi";
import {
  cancelEvalRun,
  getEvalRun,
  listEvalRuns,
  startScenarioEvalAsync,
} from "@/services/eval/scenarioApi";

import {
  formatDurationZh,
  labelEvalTier,
  labelRunStatus,
  labelVerdict,
} from "@/lib/uiLabels";

import "./test-panel.css";

const DEFAULT_FORM: EmotionEvalRequest = {
  background: "独居，最近工作压力大，睡眠质量下降。",
  initial_mood: "anxious",
  rounds: 5,
  goal: "评估助手的情绪支持质量",
};

const MOOD_OPTIONS: Array<{ value: InitialMood; label: string }> = [
  { value: "anxious", label: "焦虑" },
  { value: "sad", label: "难过" },
  { value: "angry", label: "生气" },
  { value: "lonely", label: "孤独" },
  { value: "stressed", label: "压力大" },
  { value: "neutral", label: "平静" },
];

const PANEL_TABS = [
  { id: "scenario" as const, label: "场景回归", icon: ClipboardList },
  { id: "exploratory" as const, label: "情绪探索", icon: Sparkles },
  { id: "history" as const, label: "运行历史", icon: History },
];

type PanelTab = (typeof PANEL_TABS)[number]["id"];
type ScenarioTier = "smoke" | "judge";
type HistoryTierFilter = "all" | "smoke" | "judge" | "exploratory";

function formatDuration(durationMs: number | null | undefined): string {
  return formatDurationZh(durationMs);
}

function historyItemTitle(item: EvalRunSummary): string {
  if (item.mode === "exploratory" || item.tier === "exploratory") {
    return "情绪探索";
  }
  return item.scenario_id;
}

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function clampRounds(value: number): number {
  if (!Number.isFinite(value)) {
    return DEFAULT_FORM.rounds;
  }
  return Math.min(8, Math.max(1, Math.round(value)));
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "评测运行失败";
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

export function TestPanel(): JSX.Element {
  const { state: evalRunState, dispatch: dispatchEvalRun } = useEvalRun();
  const [activeTab, setActiveTab] = useState<PanelTab>("exploratory");
  const [form, setForm] = useState<EmotionEvalRequest>(DEFAULT_FORM);
  const [scenarioTier, setScenarioTier] = useState<ScenarioTier>("smoke");
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<string[]>([]);
  const advanceInFlightRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<EvalRunSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyTierFilter, setHistoryTierFilter] = useState<HistoryTierFilter>("all");
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);

  const scenarioRunning = evalRunState.batchStatus === "running";
  const focusedItem = getFocusedItem(evalRunState);
  const focusedLive = focusedItem?.live;
  const exploratoryLive = focusedLive?.tier === "exploratory" ? focusedLive : null;
  const exploratoryRunning = scenarioRunning && exploratoryLive !== null;
  const scenarioBatchRunning = scenarioRunning && focusedLive?.tier !== "exploratory";

  const updateForm = <Key extends keyof EmotionEvalRequest>(
    key: Key,
    value: EmotionEvalRequest[Key],
  ): void => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const updateRounds = (value: number): void => {
    if (!Number.isFinite(value)) {
      return;
    }
    updateForm("rounds", clampRounds(value));
  };

  useEffect(() => {
    if (activeTab !== "history") {
      return;
    }
    let active = true;
    setHistoryLoading(true);
    const tier = historyTierFilter === "all" ? undefined : historyTierFilter;
    listEvalRuns(tier)
      .then((items) => {
        if (active) {
          setHistoryItems(items);
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(getErrorMessage(loadError));
        }
      })
      .finally(() => {
        if (active) {
          setHistoryLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [activeTab, historyTierFilter]);

  const handleExploratoryRun = async (): Promise<void> => {
    if (exploratoryRunning || scenarioBatchRunning) {
      return;
    }

    const scenario = { ...form, rounds: clampRounds(form.rounds) };
    setForm(scenario);
    setError(null);

    dispatchEvalRun({
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["exploratory"] },
    });

    try {
      const started = await startExploratoryEvalAsync(scenario, getOrCreateUserId());
      dispatchEvalRun({
        type: "RUN_STARTED",
        payload: {
          runId: started.run_id,
          scenarioId: started.scenario_id,
          tier: started.tier,
        },
      });
    } catch (runError) {
      dispatchEvalRun({ type: "RESET" });
      setError(getErrorMessage(runError));
    }
  };

  const handleExploratoryCancel = async (): Promise<void> => {
    dispatchEvalRun({ type: "BATCH_CANCEL" });
    const runningItem = getRunningItem(evalRunState);
    if (!runningItem?.live.activeRunId) {
      return;
    }
    try {
      await cancelEvalRun(runningItem.live.activeRunId);
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  const startScenarioEval = async (scenarioId: string): Promise<void> => {
    setError(null);
    const started = await startScenarioEvalAsync(scenarioId, getOrCreateUserId());
    dispatchEvalRun({
      type: "RUN_STARTED",
      payload: {
        runId: started.run_id,
        scenarioId: started.scenario_id,
        tier: started.tier,
      },
    });
  };

  const handleScenarioRun = async (): Promise<void> => {
    if (scenarioBatchRunning || exploratoryRunning || selectedScenarioIds.length === 0) {
      return;
    }

    dispatchEvalRun({
      type: "BATCH_STARTED",
      payload: { scenarioIds: selectedScenarioIds },
    });

    try {
      await startScenarioEval(selectedScenarioIds[0]);
    } catch (runError) {
      dispatchEvalRun({ type: "RESET" });
      setError(getErrorMessage(runError));
    }
  };

  const handleScenarioCancel = async (): Promise<void> => {
    dispatchEvalRun({ type: "BATCH_CANCEL" });
    const runningItem = getRunningItem(evalRunState);
    if (!runningItem?.live.activeRunId) {
      return;
    }
    try {
      await cancelEvalRun(runningItem.live.activeRunId);
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  useEffect(() => {
    if (evalRunState.batchStatus !== "running") {
      advanceInFlightRef.current = false;
      return;
    }
    if (getRunningItem(evalRunState)) {
      return;
    }
    const nextItem = getNextPendingItem(evalRunState);
    if (!nextItem || advanceInFlightRef.current) {
      return;
    }
    advanceInFlightRef.current = true;
    dispatchEvalRun({ type: "BATCH_ADVANCE" });
    startScenarioEval(nextItem.scenarioId)
      .catch((runError: unknown) => {
        dispatchEvalRun({ type: "RESET" });
        setError(getErrorMessage(runError));
      })
      .finally(() => {
        advanceInFlightRef.current = false;
      });
  }, [evalRunState.batchStatus, evalRunState.items]);

  const handleHistorySelect = async (runId: string): Promise<void> => {
    setSelectedHistoryId(runId);
    setError(null);
    try {
      const result = await getEvalRun(runId);
      dispatchEvalRun({ type: "LOAD_RESULT", payload: result });
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  const historyDetail = selectedHistoryId ? focusedLive?.liveResult : undefined;
  const scenarioError = error ?? focusedLive?.error;
  const hasScenarioResult = Boolean(focusedLive?.liveResult.scenario_id);
  const showBatchQueue = shouldShowBatchQueue(evalRunState);

  return (
    <section className="test-panel-root flex h-full min-h-0 flex-col overflow-hidden">
      <header className="affect-rail-header shrink-0">
        <div className="affect-rail-header__row">
          <h2 className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
            <span className="affect-rail-header__icon">
              <FlaskConical className="h-3.5 w-3.5" aria-hidden />
            </span>
            评测
          </h2>
          <nav aria-label="评测类型" className="test-panel-tabs" role="tablist">
            {PANEL_TABS.map((tab) => (
              <button
                aria-selected={activeTab === tab.id}
                className={`test-panel-tab${activeTab === tab.id ? " test-panel-tab--active" : ""}`}
                key={tab.id}
                role="tab"
                type="button"
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-hidden">
        {activeTab === "scenario" ? (
          <div className="test-sidebar-group h-full">
            <aside className="test-list-panel">
              <TestRailHeader
                icon={ClipboardList}
                subtitle="勾选冒烟 / 评判场景，支持多选依次运行"
                title="场景列表"
                actions={
                  <div className="test-tier-toggle">
                    {(["smoke", "judge"] as const).map((tier) => (
                      <button
                        className={`test-tier-toggle__btn${
                          scenarioTier === tier ? " test-tier-toggle__btn--active" : ""
                        }`}
                        disabled={scenarioBatchRunning}
                        key={tier}
                        type="button"
                        onClick={() => {
                          setScenarioTier(tier);
                          setSelectedScenarioIds([]);
                        }}
                      >
                        {labelEvalTier(tier)}
                      </button>
                    ))}
                  </div>
                }
              />

              <div className="flex min-h-0 flex-1 flex-col px-4 pb-4">
                <ScenarioPicker
                  key={scenarioTier}
                  disabled={scenarioBatchRunning}
                  selectedIds={selectedScenarioIds}
                  tier={scenarioTier}
                  onChange={setSelectedScenarioIds}
                />

                <button
                  className={`test-action-btn mt-3 shrink-0 ${
                    scenarioBatchRunning ? "test-action-btn--cancel" : "test-action-btn--run"
                  }`}
                  disabled={!scenarioBatchRunning && selectedScenarioIds.length === 0}
                  type="button"
                  onClick={scenarioBatchRunning ? handleScenarioCancel : handleScenarioRun}
                >
                  <span className="inline-flex items-center justify-center gap-1.5">
                    {scenarioBatchRunning ? (
                      <Square className="h-3 w-3" aria-hidden />
                    ) : (
                      <Play className="h-3 w-3" aria-hidden />
                    )}
                    {scenarioBatchRunning
                      ? "取消测试"
                      : selectedScenarioIds.length > 1
                        ? `运行 ${selectedScenarioIds.length} 个场景`
                        : "运行场景"}
                  </span>
                </button>
              </div>
            </aside>

            <div className="test-detail-panel">
              <TestRailHeader
                icon={Play}
                subtitle={
                  focusedLive?.progressMessage ??
                  (scenarioBatchRunning ? "实时推送评测进度" : "运行后在此查看进度与结果")
                }
                title="运行过程"
              />

              <div className="test-panel-scroll space-y-3">
                {scenarioError ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-[11px] text-destructive">
                    <p className="font-medium">测试失败</p>
                    <p className="mt-1 leading-snug">{scenarioError}</p>
                  </div>
                ) : null}

                {showBatchQueue ? (
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

                {focusedLive ? (
                  <>
                    <EvalRunProgressView state={focusedLive} />
                    <EvalRunResultView result={focusedLive.liveResult} />
                  </>
                ) : null}

                {!scenarioBatchRunning && !scenarioError && !hasScenarioResult ? (
                  <TestEmptyState
                    description="从左侧勾选场景并点击运行，断言与评判结果会显示在这里。"
                    icon={ClipboardList}
                    title="尚未开始评测"
                  />
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "exploratory" ? (
          <div className="test-sidebar-group h-full">
            <aside className="test-list-panel">
              <TestRailHeader
                icon={Sparkles}
                subtitle="配置模拟用户，评估情绪支持质量"
                title="探索配置"
              />

              <div className="test-panel-scroll space-y-3">
                <label className="flex flex-col gap-1.5">
                  <span className="text-[11px] font-medium text-muted-foreground">用户背景</span>
                  <textarea
                    className="min-h-28 rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] leading-relaxed text-foreground outline-none transition-colors duration-200 focus:border-border"
                    disabled={exploratoryRunning}
                    value={form.background}
                    onChange={(event) => updateForm("background", event.target.value)}
                  />
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-[11px] font-medium text-muted-foreground">初始心情</span>
                  <select
                    className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
                    disabled={exploratoryRunning}
                    value={form.initial_mood}
                    onChange={(event) =>
                      updateForm("initial_mood", event.target.value as InitialMood)
                    }
                  >
                    {MOOD_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="grid grid-cols-2 gap-2">
                  <label className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-medium text-muted-foreground">测试轮次</span>
                    <input
                      className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
                      disabled={exploratoryRunning}
                      max={8}
                      min={1}
                      type="number"
                      value={form.rounds}
                      onChange={(event) => updateRounds(event.target.valueAsNumber)}
                    />
                  </label>

                  <label className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-medium text-muted-foreground">测试目标</span>
                    <input
                      className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
                      disabled={exploratoryRunning}
                      value={form.goal}
                      onChange={(event) => updateForm("goal", event.target.value)}
                    />
                  </label>
                </div>

                <button
                  className={`test-action-btn ${
                    exploratoryRunning ? "test-action-btn--cancel" : "test-action-btn--run"
                  }`}
                  type="button"
                  onClick={exploratoryRunning ? handleExploratoryCancel : handleExploratoryRun}
                >
                  <span className="inline-flex items-center justify-center gap-1.5">
                    {exploratoryRunning ? (
                      <Square className="h-3 w-3" aria-hidden />
                    ) : (
                      <Play className="h-3 w-3" aria-hidden />
                    )}
                    {exploratoryRunning ? "取消测试" : "开始测试"}
                  </span>
                </button>
              </div>
            </aside>

            <div className="test-detail-panel">
              <TestRailHeader
                icon={Sparkles}
                subtitle={
                  exploratoryLive?.progressMessage ??
                  (exploratoryRunning ? "实时推送探索进度" : "运行后在此查看进度与结果")
                }
                title="探索过程"
              />

              <div className="test-panel-scroll space-y-3">
                {error && activeTab === "exploratory" ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-[11px] text-destructive">
                    <p className="font-medium">测试失败</p>
                    <p className="mt-1 leading-snug">{error}</p>
                  </div>
                ) : null}

                {exploratoryLive ? <EvalRunProgressView state={exploratoryLive} /> : null}

                {exploratoryLive?.liveResult.summary ? (
                  <section className="rounded-lg border border-border/30 border-l-[3px] border-l-emerald-500/45 bg-emerald-500/[0.04] px-3.5 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                          总分
                        </p>
                        <p className="text-xl font-semibold text-foreground">
                          {formatScore(exploratoryLive.liveResult.summary.overall_score)}
                        </p>
                      </div>
                      <span className="test-status-badge test-status-badge--neutral">
                        {labelVerdict(exploratoryLive.liveResult.summary.verdict)}
                      </span>
                    </div>
                    <p className="mt-2 text-[11px] leading-snug text-muted-foreground">
                      {exploratoryLive.liveResult.summary.conclusion}
                    </p>
                    {(exploratoryLive.liveResult.summary.improvement_suggestions?.length ?? 0) >
                    0 ? (
                      <ul className="mt-2 list-disc space-y-0.5 pl-4 text-[11px] text-muted-foreground">
                        {exploratoryLive.liveResult.summary.improvement_suggestions?.map(
                          (suggestion) => (
                            <li key={suggestion}>{suggestion}</li>
                          ),
                        )}
                      </ul>
                    ) : null}
                  </section>
                ) : null}

                {(exploratoryLive?.liveResult.scores?.length ?? 0) > 0 ? (
                  <section className="rounded-lg border border-border/30 border-l-[3px] border-l-indigo-500/45 bg-indigo-500/[0.04] px-3.5 py-3">
                    <h4 className="mb-2 text-[13px] font-medium text-foreground">指标评分</h4>
                    <ul className="space-y-2">
                      {exploratoryLive?.liveResult.scores?.map((metric) => (
                        <li
                          className="rounded-md border border-border/25 bg-background/40 px-2.5 py-2"
                          key={metric.name}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-[11px] font-medium text-foreground/90">
                              {metric.name}
                            </p>
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

                {(exploratoryLive?.liveResult.observations?.length ?? 0) > 0 ? (
                  <section className="rounded-lg border border-border/30 border-l-[3px] border-l-violet-500/45 bg-violet-500/[0.04] px-3.5 py-3">
                    <h4 className="mb-2 text-[13px] font-medium text-foreground">对话轮次</h4>
                    <ul className="space-y-2">
                      {exploratoryLive?.liveResult.observations?.map((turn) => (
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

                {!exploratoryRunning && !(error && activeTab === "exploratory") && !exploratoryLive ? (
                  <TestEmptyState
                    description="填写左侧配置并点击开始测试，进度与评分将实时显示在这里。"
                    icon={Sparkles}
                    title="等待探索评测"
                  />
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "history" ? (
          <div className="test-sidebar-group h-full">
            <aside className="test-list-panel">
              <TestRailHeader icon={History} subtitle="评测运行记录持久化存储" title="历史列表" />

              <div className="border-b border-border/25 bg-muted/10 px-2 py-2">
                <div className="flex flex-wrap gap-1">
                  {(["all", "smoke", "judge", "exploratory"] as const).map((tier) => (
                    <button
                      className={`cursor-pointer rounded-md px-2 py-1 text-[10px] transition-colors duration-200 ${
                        historyTierFilter === tier
                          ? "bg-muted/50 text-foreground"
                          : "text-muted-foreground hover:bg-muted/30"
                      }`}
                      key={tier}
                      type="button"
                      onClick={() => setHistoryTierFilter(tier)}
                    >
                      {labelEvalTier(tier)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="test-panel-scroll space-y-1.5">
                {historyLoading ? (
                  <p className="flex items-center justify-center gap-1.5 py-8 text-[11px] text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden />
                    加载中…
                  </p>
                ) : (
                  <>
                    {historyItems.map((item) => (
                      <button
                        aria-pressed={selectedHistoryId === item.run_id}
                        className={`w-full cursor-pointer rounded-md border px-3 py-2.5 text-left transition-colors duration-200 ${
                          selectedHistoryId === item.run_id
                            ? "border-border bg-muted/35"
                            : "border-transparent bg-transparent hover:bg-muted/25"
                        }`}
                        key={item.run_id}
                        type="button"
                        onClick={() => void handleHistorySelect(item.run_id)}
                      >
                        <div className="flex items-baseline justify-between gap-2">
                          <p className="truncate text-xs font-medium text-foreground/90">
                            {historyItemTitle(item)}
                          </p>
                          <span className="shrink-0 text-[10px] text-muted-foreground">
                            {labelEvalTier(item.tier)}
                          </span>
                        </div>
                        <p className="mt-1 text-[10px] text-muted-foreground">
                          {labelRunStatus(item.status)}
                          {item.duration_ms ? ` · ${formatDuration(item.duration_ms)}` : ""}
                          {item.finished_at ? ` · ${item.finished_at.slice(0, 19)}` : ""}
                        </p>
                      </button>
                    ))}
                    {historyItems.length === 0 ? (
                      <TestEmptyState
                        description="运行场景回归或情绪探索后，记录会出现在这里。"
                        icon={History}
                        title="暂无历史记录"
                      />
                    ) : null}
                  </>
                )}
              </div>
            </aside>

            <div className="test-detail-panel">
              <TestRailHeader icon={History} subtitle="选中记录查看详情" title="历史详情" />

              <div className="test-panel-scroll space-y-3">
                {scenarioError ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-[11px] text-destructive">
                    <p className="font-medium">加载失败</p>
                    <p className="mt-1 leading-snug">{scenarioError}</p>
                  </div>
                ) : null}

                {historyDetail ? (
                  <>
                    <EvalRunTelemetryView result={historyDetail} />
                    <EvalRunHistoryTimeline
                      events={historyDetail.events}
                      scenarioId={historyDetail.scenario_id}
                      status={historyDetail.status}
                      tier={historyDetail.tier}
                    />
                    <EvalRunResultView result={historyDetail} />
                  </>
                ) : null}

                {!scenarioError && !historyDetail ? (
                  <TestEmptyState
                    description="从左侧选择一条运行记录，完整评测结果将显示在这里。"
                    icon={History}
                    title="未选择记录"
                  />
                ) : null}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
