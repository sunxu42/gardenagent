import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import type { EvalRunPhase, EvalTimelineEntry } from "@/features/test/evalProgress";
import type { LiveEvalRunState } from "@/features/test/evalRunStore";
import { labelEvalTier } from "@/lib/uiLabels";

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
    return "border-emerald-500/30 bg-emerald-500/[0.06]";
  }
  if (tone === "warning") {
    return "border-amber-500/30 bg-amber-500/[0.06]";
  }
  if (tone === "error") {
    return "border-destructive/30 bg-destructive/5";
  }
  return "border-border/25 bg-background/40";
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
}

export function EvalRunProgressView({
  state,
  readOnly = false,
}: EvalRunProgressViewProps): JSX.Element | null {
  const isRunning = !readOnly && state.status === "running";
  const currentIndex = phaseIndex(state.phase);
  const hasActivity = isRunning || state.timeline.length > 0;

  if (!hasActivity) {
    return null;
  }

  return (
    <div className="space-y-3">
      <section className="rounded-lg border border-border/30 bg-muted/15 px-3.5 py-3">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {PHASE_STEPS.map((step, index) => {
            const done = readOnly
              ? currentIndex >= index && state.phase !== "failed" && state.phase !== "cancelled"
              : currentIndex > index;
            const active = !readOnly && currentIndex === index && isRunning;
            const failed = state.phase === "failed" && index === 4;
            const cancelled = state.phase === "cancelled" && index === 4;
            const terminalDone = readOnly && state.phase === "completed" && index === 4;
            return (
              <div className="flex items-center gap-1.5" key={step.id}>
                {done || terminalDone ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" aria-hidden />
                ) : active ? (
                  <Loader2
                    className="h-3.5 w-3.5 animate-spin text-primary motion-reduce:animate-none"
                    aria-hidden
                  />
                ) : failed || cancelled ? (
                  <XCircle className="h-3.5 w-3.5 text-destructive" aria-hidden />
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

        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              当前状态
            </p>
            <p className="mt-0.5 text-[12px] font-medium text-foreground">
              {state.progressMessage ?? "等待进度…"}
            </p>
            {state.scenarioId ? (
              <p className="mt-1 truncate text-[10px] text-muted-foreground">
                {state.scenarioId}
                {state.tier ? ` · ${labelEvalTier(state.tier)}` : ""}
              </p>
            ) : null}
          </div>
          {isRunning ? (
            <Loader2
              className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary motion-reduce:animate-none"
              aria-hidden
            />
          ) : null}
        </div>

        {state.agentProgress ? (
          <p className="mt-2 text-[10px] text-muted-foreground">
            对话进度 {state.agentProgress.current}/{state.agentProgress.total}
          </p>
        ) : null}
        {state.judgeProgress ? (
          <p className="mt-1 text-[10px] text-muted-foreground">
            评判进度 {state.judgeProgress.current}/{state.judgeProgress.total}
          </p>
        ) : null}
      </section>

      {state.timeline.length > 0 ? (
        <section className="rounded-lg border border-border/30 border-l-[3px] border-l-sky-500/45 bg-sky-500/[0.04] px-3.5 py-3">
          <h4 className="mb-2 text-[13px] font-medium text-foreground">
            {readOnly ? "过程记录" : "实时日志"}
          </h4>
          <ul className="max-h-56 space-y-2 overflow-y-auto pr-1">
            {[...state.timeline].reverse().map((entry) => (
              <li
                className={`rounded-md border px-2.5 py-2 ${toneClassName(entry.tone)}`}
                key={entry.id}
              >
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
      ) : null}
    </div>
  );
}
