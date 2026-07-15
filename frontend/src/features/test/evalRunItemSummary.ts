import {
  Ban,
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";
import { createElement, type ReactElement } from "react";

import type { BatchEvalItem } from "@/features/test/evalBatchTypes";

export function formatEvalItemSummary(item: BatchEvalItem): string {
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

export function EvalRunStatusIcon({ item }: { item: BatchEvalItem }): ReactElement {
  if (item.status === "running") {
    return createElement(Loader2, {
      className: "test-text-run h-3.5 w-3.5 shrink-0 animate-spin motion-reduce:animate-none",
      "aria-hidden": true,
    });
  }
  if (item.status === "completed") {
    return createElement(CheckCircle2, {
      className: "h-3.5 w-3.5 shrink-0 text-primary",
      "aria-hidden": true,
    });
  }
  if (item.status === "failed") {
    return createElement(XCircle, {
      className: "h-3.5 w-3.5 shrink-0 text-destructive",
      "aria-hidden": true,
    });
  }
  if (item.status === "cancelled") {
    return createElement(Ban, {
      className: "h-3.5 w-3.5 shrink-0 text-muted-foreground",
      "aria-hidden": true,
    });
  }
  return createElement(Circle, {
    className: "h-3.5 w-3.5 shrink-0 text-muted-foreground/50",
    "aria-hidden": true,
  });
}
