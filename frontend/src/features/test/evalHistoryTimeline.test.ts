import { describe, expect, it } from "vitest";

import { eventsToTimeline } from "@/features/test/evalHistoryTimeline";

describe("eventsToTimeline", () => {
  it("maps eval_progress to info entry", () => {
    const timeline = eventsToTimeline([
      {
        type: "eval_progress",
        at: "2026-06-23T10:00:00Z",
        payload: { message: "第 1/3 轮" },
      },
    ]);
    expect(timeline).toHaveLength(1);
    expect(timeline[0].title).toContain("第 1/3 轮");
  });
});
