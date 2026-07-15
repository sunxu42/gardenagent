import { describe, expect, it } from "vitest";
import { mapAguiEvent } from "../../services/agui/mapAguiEvent";

describe("mapAguiEvent", () => {
  it("maps RUN_STARTED to aguiRunStarted", () => {
    const action = mapAguiEvent(
      { type: "RUN_STARTED", messageId: "msg-1", runId: "run-1" },
      "msg-1",
    );
    expect(action).toEqual({
      type: "aguiRunStarted",
      payload: { messageId: "msg-1", runId: "run-1" },
    });
  });

  it("maps TEXT_MESSAGE_CONTENT to aguiTextDelta", () => {
    const action = mapAguiEvent(
      { type: "TEXT_MESSAGE_CONTENT", messageId: "msg-1", runId: "run-1", delta: "Hi" },
      "msg-1",
    );
    expect(action?.type).toBe("aguiTextDelta");
    if (action?.type === "aguiTextDelta") {
      expect(action.payload.delta).toBe("Hi");
    }
  });

  it("drops events when assistant message id mismatches", () => {
    const action = mapAguiEvent(
      { type: "RUN_FINISHED", messageId: "msg-1", runId: "run-1" },
      "msg-2",
    );
    expect(action).toBeNull();
  });

  it("maps A2UI_OPERATIONS to aguiA2uiOps", () => {
    const action = mapAguiEvent(
      {
        type: "A2UI_OPERATIONS",
        messageId: "msg-1",
        runId: "run-1",
        surfaceId: "surface-1",
        operations: [{ component: "Card", text: "请选择方案" }],
      },
      "msg-1",
    );
    expect(action).toEqual({
      type: "aguiA2uiOps",
      payload: {
        messageId: "msg-1",
        runId: "run-1",
        surfaceId: "surface-1",
        operations: [{ component: "Card", text: "请选择方案" }],
      },
    });
  });
});
