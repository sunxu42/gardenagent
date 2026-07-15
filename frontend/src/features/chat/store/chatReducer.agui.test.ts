import { describe, expect, it } from "vitest";
import type { ChatState } from "../types";
import { initialChatState, chatReducer } from "./chatReducer";

describe("chatReducer agui", () => {
  it("streams text via agui actions", () => {
    let state: ChatState = {
      ...initialChatState,
      messages: [
        {
          id: "assistant-1",
          role: "assistant",
          parts: [{ type: "text", text: "" }],
          content: "",
          status: "sending",
        },
      ],
    };

    state = chatReducer(state, {
      type: "aguiRunStarted",
      payload: { messageId: "assistant-1", runId: "run-1" },
    });
    expect(state.messages[0]?.status).toBe("streaming");
    expect(state.messages[0]?.runId).toBe("run-1");

    state = chatReducer(state, {
      type: "aguiTextDelta",
      payload: { messageId: "assistant-1", runId: "run-1", delta: "你好" },
    });
    expect(state.messages[0]?.content).toBe("你好");

    state = chatReducer(state, {
      type: "aguiA2uiOps",
      payload: {
        messageId: "assistant-1",
        runId: "run-1",
        surfaceId: "plan-selector",
        operations: [
          {
            version: "v0.9",
            createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
          },
        ],
      },
    });
    const pendingPart = state.messages[0]?.parts.find((part) => part.type === "a2ui");
    expect(pendingPart?.type).toBe("a2ui");
    if (pendingPart?.type === "a2ui") {
      expect(pendingPart.interaction).toBe("pending");
    }

    state = chatReducer(state, {
      type: "aguiTextDelta",
      payload: { messageId: "assistant-1", runId: "run-1", delta: "请确认方案。" },
    });
    expect(state.messages[0]?.parts.map((part) => part.type)).toEqual(["text", "a2ui", "text"]);

    state = chatReducer(state, {
      type: "aguiRunFinished",
      payload: { messageId: "assistant-1", runId: "run-1" },
    });
    expect(state.messages[0]?.status).toBe("done");
    const a2uiPart = state.messages[0]?.parts.find((part) => part.type === "a2ui");
    expect(a2uiPart?.type).toBe("a2ui");
    if (a2uiPart?.type === "a2ui") {
      expect(a2uiPart.status).toBe("ready");
      expect(a2uiPart.interaction).toBe("pending");
    }
  });

  it("keeps pending interaction until resolved explicitly", () => {
    let state: ChatState = {
      ...initialChatState,
      messages: [
        {
          id: "assistant-1",
          role: "assistant",
          parts: [{ type: "text", text: "" }],
          content: "",
          status: "streaming",
          runId: "run-1",
        },
      ],
    };

    state = chatReducer(state, {
      type: "aguiA2uiOps",
      payload: {
        messageId: "assistant-1",
        runId: "run-1",
        surfaceId: "plan-selector",
        operations: [
          {
            version: "v0.9",
            createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
          },
        ],
      },
    });

    state = chatReducer(state, {
      type: "a2uiInteractionResolved",
      payload: {
        messageId: "assistant-1",
        surfaceId: "plan-selector",
        action: { name: "confirm_plan", context: { planId: "plan-a" } },
      },
    });

    const a2uiPart = state.messages[0]?.parts.find((part) => part.type === "a2ui");
    if (a2uiPart?.type === "a2ui") {
      expect(a2uiPart.interaction).toBe("resolved");
      const lastOp = a2uiPart.messages.at(-1);
      expect(lastOp).toEqual({
        version: "v0.9",
        updateDataModel: {
          surfaceId: "plan-selector",
          path: "/selectedPlan",
          value: "plan-a",
        },
      });
    }
  });

  it("resumes streaming on the same assistant message after UI action", () => {
    let state: ChatState = {
      ...initialChatState,
      messages: [
        {
          id: "assistant-1",
          role: "assistant",
          parts: [
            { type: "text", text: "请选一个方案。" },
            {
              type: "a2ui",
              surfaceId: "plan-selector",
              messages: [],
              status: "ready",
              interaction: "resolved",
            },
          ],
          content: "请选一个方案。",
          status: "done",
          runId: "run-1",
        },
      ],
    };

    state = chatReducer(state, {
      type: "aguiRunStarted",
      payload: { messageId: "assistant-1", runId: "run-2" },
    });
    expect(state.messages[0]?.status).toBe("streaming");
    expect(state.messages[0]?.runId).toBe("run-2");
    expect(state.messages[0]?.parts).toHaveLength(2);

    state = chatReducer(state, {
      type: "aguiTextDelta",
      payload: {
        messageId: "assistant-1",
        runId: "run-2",
        delta: "好的，我们开始。",
      },
    });
    expect(state.messages[0]?.content).toContain("好的，我们开始。");
  });
});
