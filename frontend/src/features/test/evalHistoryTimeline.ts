import type { EvalTimelineEntry } from "@/features/test/evalProgress";
import type { PersistedEventDTO } from "@/features/test/types";

function eventTitle(event: PersistedEventDTO): string {
  const payload = event.payload ?? {};
  if (typeof payload.message === "string" && payload.message.length > 0) {
    return payload.message;
  }
  if (event.type === "eval_started") {
    return "评测已开始";
  }
  if (event.type === "eval_turn") {
    return `第 ${String(payload.round ?? "?")} 轮对话完成`;
  }
  if (event.type === "eval_assertions") {
    return "基础断言完成";
  }
  if (event.type === "eval_judge_metric") {
    return `评判 · ${String(payload.name ?? "指标")}`;
  }
  if (event.type === "eval_completed") {
    return "评测完成";
  }
  if (event.type === "eval_failed") {
    return "评测失败";
  }
  if (event.type === "eval_cancelled") {
    return "评测已取消";
  }
  return event.type;
}

function eventTone(event: PersistedEventDTO): EvalTimelineEntry["tone"] {
  if (event.type === "eval_failed") {
    return "error";
  }
  if (event.type === "eval_completed") {
    return "success";
  }
  if (event.type === "eval_cancelled") {
    return "warning";
  }
  if (event.type === "eval_judge_metric") {
    return payloadPassed(event) ? "success" : "warning";
  }
  return "info";
}

function payloadPassed(event: PersistedEventDTO): boolean {
  const passed = event.payload?.passed;
  return passed === true;
}

export function eventsToTimeline(events: PersistedEventDTO[]): EvalTimelineEntry[] {
  return events.map((event, index) => ({
    id: `hist-${index}-${event.at}`,
    at: Date.parse(event.at) || index,
    tone: eventTone(event),
    title: eventTitle(event),
    detail:
      event.type === "eval_judge_metric" && typeof event.payload?.reason === "string"
        ? event.payload.reason
        : undefined,
  }));
}
