import type { EvalWsEvent } from "@/features/test/evalWsTypes";
import { labelAssertionStatus } from "@/lib/uiLabels";

export type EvalRunPhase =
  | "idle"
  | "starting"
  | "agent"
  | "assertions"
  | "judge"
  | "completed"
  | "failed"
  | "cancelled";

export interface EvalTimelineEntry {
  id: string;
  at: number;
  tone: "info" | "success" | "warning" | "error";
  title: string;
  detail?: string;
}

export interface EvalProgressSnapshot {
  phase: EvalRunPhase;
  message: string | null;
  agentProgress: { current: number; total: number } | null;
  judgeProgress: { current: number; total: number } | null;
  timeline: EvalTimelineEntry[];
}

export function createInitialEvalProgress(): EvalProgressSnapshot {
  return {
    phase: "idle",
    message: null,
    agentProgress: null,
    judgeProgress: null,
    timeline: [],
  };
}

function nextTimelineId(timeline: EvalTimelineEntry[]): string {
  return `tl-${timeline.length}-${Date.now()}`;
}

function appendTimeline(
  timeline: EvalTimelineEntry[],
  entry: Omit<EvalTimelineEntry, "id" | "at">,
): EvalTimelineEntry[] {
  return [
    ...timeline,
    {
      ...entry,
      id: nextTimelineId(timeline),
      at: Date.now(),
    },
  ].slice(-80);
}

function phaseFromEvent(event: EvalWsEvent): EvalRunPhase | null {
  if (event.type === "eval_started") {
    return "agent";
  }
  if (event.type === "eval_progress" && event.phase === "setup") {
    return "starting";
  }
  if (event.type === "eval_progress" && event.phase) {
    if (event.phase === "agent") {
      return "agent";
    }
    if (event.phase === "assertions") {
      return "assertions";
    }
    if (event.phase === "judge") {
      return "judge";
    }
  }
  if (event.type === "eval_assertions") {
    return "assertions";
  }
  if (event.type === "eval_judge_metric") {
    return "judge";
  }
  if (event.type === "eval_completed") {
    return event.status === "failed" ? "failed" : "completed";
  }
  if (event.type === "eval_failed") {
    return "failed";
  }
  if (event.type === "eval_cancelled") {
    return "cancelled";
  }
  return null;
}

export function applyEvalWsProgress(
  progress: EvalProgressSnapshot,
  event: EvalWsEvent,
): EvalProgressSnapshot {
  let next: EvalProgressSnapshot = { ...progress };
  const phase = phaseFromEvent(event);
  if (phase) {
    next.phase = phase;
  }

  if (event.type === "eval_started") {
    next.message = event.description ?? `场景 ${event.scenario_id ?? ""} 已启动`;
    next.timeline = appendTimeline(next.timeline, {
      tone: "info",
      title: "评测已启动",
      detail: event.description ?? event.scenario_id,
    });
    return next;
  }

  if (event.type === "eval_progress") {
    if (event.message) {
      next.message = event.message;
    }
    if (event.phase === "setup") {
      next.timeline = appendTimeline(next.timeline, {
        tone: "info",
        title: event.message ?? "准备中…",
        detail:
          event.reused_agent === true
            ? "复用已初始化的评测助手"
            : event.reused_agent === false
              ? "首次初始化评测助手"
              : undefined,
      });
      return next;
    }
    if (event.round != null && event.total_rounds != null) {
      next.agentProgress = { current: event.round, total: event.total_rounds };
    }
    if (event.judge_index != null && event.judge_total != null) {
      next.judgeProgress = { current: event.judge_index, total: event.judge_total };
    }
    if (event.message) {
      next.timeline = appendTimeline(next.timeline, {
        tone: "info",
        title: event.message,
        detail: typeof event.user === "string" ? `用户：${event.user}` : undefined,
      });
    }
    return next;
  }

  if (event.type === "eval_turn" && event.round != null && event.user != null) {
    next.agentProgress = next.agentProgress ?? {
      current: event.round,
      total: event.round,
    };
    next.message = `第 ${event.round} 轮对话已完成`;
    next.timeline = appendTimeline(next.timeline, {
      tone: "success",
      title: `第 ${event.round} 轮完成`,
      detail: `用户：${event.user}\n助手：${event.assistant ?? "（无回复）"}`,
    });
    return next;
  }

  if (event.type === "eval_assertions" && event.assertions) {
    const failed = event.assertions.filter((item) => item.status === "fail").length;
    const passed = event.assertions.length - failed;
    next.message = `基础断言：${passed} 通过，${failed} 失败`;
    next.timeline = appendTimeline(next.timeline, {
      tone: failed > 0 ? "warning" : "success",
      title: "基础断言完成",
      detail: event.assertions
        .map((item) => `${item.name}: ${labelAssertionStatus(item.status)}`)
        .join(" · "),
    });
    return next;
  }

  if (event.type === "eval_judge_metric" && event.name) {
    next.message = `评判 · ${event.name}：${Math.round((event.score ?? 0) * 100)}%`;
    next.timeline = appendTimeline(next.timeline, {
      tone: event.passed ? "success" : "warning",
      title: `评判 ${event.name}`,
      detail: event.reason ?? undefined,
    });
    return next;
  }

  if (event.type === "eval_completed") {
    next.message =
      event.status === "failed" ? "评测未通过" : "评测已完成";
    next.timeline = appendTimeline(next.timeline, {
      tone: event.status === "failed" ? "error" : "success",
      title: next.message,
      detail:
        event.judge_overall_passed == null
          ? undefined
          : `评判总评：${event.judge_overall_passed ? "通过" : "未通过"}`,
    });
    return next;
  }

  if (event.type === "eval_failed") {
    next.message = event.error?.message ?? "评测失败";
    next.timeline = appendTimeline(next.timeline, {
      tone: "error",
      title: "评测失败",
      detail: event.error?.message,
    });
    return next;
  }

  if (event.type === "eval_cancelled") {
    next.message = "评测已取消";
    next.timeline = appendTimeline(next.timeline, {
      tone: "warning",
      title: "评测已取消",
    });
    return next;
  }

  return next;
}
