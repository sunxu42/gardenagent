import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import { TestPanelCollapsibleSection } from "@/features/test/TestPanelCollapsibleSection";
import type { EvalRunPhase, EvalTimelineEntry } from "@/features/test/evalProgress";
import type { LiveEvalRunState } from "@/features/test/evalRunStore";
import { cn } from "@/lib/utils";

const PHASE_STEPS: Array<{ id: EvalRunPhase; label: string }> = [
  { id: "starting", label: "启动" },
  { id: "agent", label: "对话" },
  { id: "assertions", label: "断言" },
  { id: "judge", label: "评判" },
  { id: "completed", label: "完成" },
];

function phaseIndex(phase: EvalRunPhase): number {
  if (phase === "starting") {
    return 0;
  }
  if (phase === "agent") {
    return 1;
  }
  if (phase === "assertions") {
    return 2;
  }
  if (phase === "judge") {
    return 3;
  }
  if (phase === "completed" || phase === "failed" || phase === "cancelled") {
    return 4;
  }
  return -1;
}

function toneClassName(tone: EvalTimelineEntry["tone"]): string {
  if (tone === "success") {
    return "test-panel-timeline-item test-panel-timeline-item--success";
  }
  if (tone === "warning") {
    return "test-panel-timeline-item test-panel-timeline-item--warning";
  }
  if (tone === "error") {
    return "test-panel-timeline-item test-panel-timeline-item--error";
  }
  return "test-panel-timeline-item";
}

interface EvalRunProgressViewProps {
  state: Pick<
    LiveEvalRunState,
    | "status"
    | "progressMessage"
    | "phase"
    | "agentProgress"
    | "judgeProgress"
    | "timeline"
    | "scenarioId"
    | "tier"
  >;
  readOnly?: boolean;
  /** compact: dock 内嵌 — 完成后仅保留可折叠日志，运行中仅步骤条 */
  variant?: "full" | "compact";
}

export function EvalRunProgressView({
  state,
  readOnly = false,
  variant = "full",
}: EvalRunProgressViewProps): JSX.Element | null {
  const isRunning = !readOnly && state.status === "running";
  const isTerminal =
    state.phase === "completed" || state.phase === "failed" || state.phase === "cancelled";
  const hasTimeline = state.timeline.length > 0;
  const hasActivity = isRunning || hasTimeline;

  if (!hasActivity) {
    return null;
  }

  if (variant === "compact" && isTerminal && hasTimeline) {
    return (
      <TestPanelCollapsibleSection defaultOpen={false} title="运行日志">
        <ul className="max-h-48 space-y-2 overflow-y-auto pr-1">
          {[...state.timeline].reverse().map((entry) => (
            <li className={toneClassName(entry.tone)} key={entry.id}>
              <p className="text-[11px] font-medium text-foreground/90">{entry.title}</p>
              {entry.detail ? (
                <p className="mt-1 whitespace-pre-wrap text-[10px] leading-snug text-muted-foreground">
                  {entry.detail}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </TestPanelCollapsibleSection>
    );
  }

  if (variant === "compact" && isTerminal && !hasTimeline) {
    return null;
  }

  const currentIndex = phaseIndex(state.phase);
  const showLivePanel = isRunning || variant === "full";
  const timelineTitle = readOnly ? "过程记录" : isRunning ? "实时日志" : "运行日志";
  const timelineDefaultOpen = variant === "compact" ? isRunning : !isTerminal;

  return (
    <div className="space-y-3">
      {showLivePanel ? (
        <section className="test-panel-section">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            {PHASE_STEPS.map((step, index) => {
              const isTerminalStep = index === PHASE_STEPS.length - 1;
              const done = readOnly
                ? currentIndex >= index && state.phase !== "failed" && state.phase !== "cancelled"
                : currentIndex > index || (isTerminalStep && state.phase === "completed");
              const active = !readOnly && currentIndex === index && isRunning;
              const failed = state.phase === "failed" && isTerminalStep;
              const cancelled = state.phase === "cancelled" && isTerminalStep;
              return (
                <div className="flex items-center gap-1.5" key={step.id}>
                  {done ? (
                    <CheckCircle2 className="test-text-pass h-3.5 w-3.5" aria-hidden />
                  ) : active ? (
                    <Loader2
                      className="test-text-run h-3.5 w-3.5 animate-spin motion-reduce:animate-none"
                      aria-hidden
                    />
                  ) : failed || cancelled ? (
                    <XCircle className="test-text-fail h-3.5 w-3.5" aria-hidden />
                  ) : (
                    <Circle className="h-3.5 w-3.5 text-muted-foreground/50" aria-hidden />
                  )}
                  <span
                    className={`text-[10px] font-medium ${
                      active ? "text-foreground" : "text-muted-foreground"
                    }`}
                  >
                    {step.label}
                  </span>
                  {index < PHASE_STEPS.length - 1 ? (
                    <span className="mx-0.5 text-[10px] text-border">›</span>
                  ) : null}
                </div>
              );
            })}
          </div>

          {variant === "full" ? (
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="test-panel-section__eyebrow">当前状态</p>
                <p className="mt-0.5 text-[12px] font-medium text-foreground">
                  {state.progressMessage ?? "等待进度…"}
                </p>
                {state.scenarioId ? (
                  <p className="mt-1 truncate text-[10px] text-muted-foreground">{state.scenarioId}</p>
                ) : null}
              </div>
              {isRunning ? (
                <Loader2
                  className="test-text-run mt-0.5 h-4 w-4 shrink-0 animate-spin motion-reduce:animate-none"
                  aria-hidden
                />
              ) : null}
            </div>
          ) : null}

          {state.agentProgress ? (
            <p className={cn("text-[10px] text-muted-foreground", variant === "full" ? "mt-2" : "")}>
              对话进度 {state.agentProgress.current}/{state.agentProgress.total}
            </p>
          ) : null}
          {state.judgeProgress ? (
            <p className="mt-1 text-[10px] text-muted-foreground">
              评判进度 {state.judgeProgress.current}/{state.judgeProgress.total}
            </p>
          ) : null}
        </section>
      ) : null}

      {hasTimeline ? (
        variant === "compact" ? (
          <TestPanelCollapsibleSection defaultOpen={timelineDefaultOpen} title={timelineTitle}>
            <ul className="max-h-48 space-y-2 overflow-y-auto pr-1">
              {[...state.timeline].reverse().map((entry) => (
                <li className={toneClassName(entry.tone)} key={entry.id}>
                  <p className="text-[11px] font-medium text-foreground/90">{entry.title}</p>
                  {entry.detail ? (
                    <p className="mt-1 whitespace-pre-wrap text-[10px] leading-snug text-muted-foreground">
                      {entry.detail}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </TestPanelCollapsibleSection>
        ) : (
          <section className="test-panel-section">
            <h4 className="test-panel-section__title">{timelineTitle}</h4>
            <ul className="max-h-56 space-y-2 overflow-y-auto pr-1">
              {[...state.timeline].reverse().map((entry) => (
                <li className={toneClassName(entry.tone)} key={entry.id}>
                  <p className="text-[11px] font-medium text-foreground/90">{entry.title}</p>
                  {entry.detail ? (
                    <p className="mt-1 whitespace-pre-wrap text-[10px] leading-snug text-muted-foreground">
                      {entry.detail}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        )
      ) : null}
    </div>
  );
}
