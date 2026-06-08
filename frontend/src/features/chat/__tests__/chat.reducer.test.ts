import { describe, expect, it } from "vitest";
import { chatReducer, initialChatState } from "../store/chatReducer";

describe("chatReducer", () => {
  it("ignores messageStreamStart on a completed assistant message", () => {
    const state = {
      ...initialChatState,
      messages: [
        {
          id: "assistant-1",
          role: "assistant" as const,
          content: "上一轮完整回复",
          status: "done" as const,
        },
      ],
    };

    const next = chatReducer(state, {
      type: "messageStreamStart",
      payload: { id: "assistant-1" },
    });

    expect(next).toBe(state);
    expect(next.messages[0]?.content).toBe("上一轮完整回复");
  });

  it("clears content on messageStreamStart for in-flight assistant message", () => {
    const state = {
      ...initialChatState,
      messages: [
        {
          id: "assistant-1",
          role: "assistant" as const,
          content: "占位",
          status: "sending" as const,
        },
      ],
    };

    const next = chatReducer(state, {
      type: "messageStreamStart",
      payload: { id: "assistant-1" },
    });

    expect(next.messages[0]?.status).toBe("streaming");
    expect(next.messages[0]?.content).toBe("");
  });
});
