import { describe, expect, it } from "vitest";
import {
  appendTextDelta,
  createMessageFromText,
  getMessageText,
  hasVisibleMessageContent,
  isAssistantThinking,
} from "./messageParts";
import type { A2uiPart } from "../types";

describe("messageParts thinking state", () => {
  it("treats empty streaming assistant as thinking", () => {
    const message = createMessageFromText("assistant-1", "assistant", "", "streaming");
    expect(hasVisibleMessageContent(message)).toBe(false);
    expect(isAssistantThinking(message)).toBe(true);
  });

  it("stops thinking once assistant text arrives", () => {
    const message = appendTextDelta(
      createMessageFromText("assistant-1", "assistant", "", "streaming"),
      "你好",
    );
    expect(hasVisibleMessageContent(message)).toBe(true);
    expect(isAssistantThinking(message)).toBe(false);
  });
});

describe("messageParts mixed layout", () => {
  it("appends text after an a2ui part as a new text segment", () => {
    const a2uiPart: A2uiPart = {
      type: "a2ui",
      surfaceId: "plan-selector",
      status: "ready",
      messages: [],
    };
    let message = createMessageFromText("assistant-1", "assistant", "上文：");
    message = {
      ...message,
      parts: [message.parts[0], a2uiPart],
    };
    message = appendTextDelta(message, "下文确认。");

    expect(getMessageText(message)).toBe("上文：下文确认。");
    expect(message.parts.map((part) => part.type)).toEqual(["text", "a2ui", "text"]);
    expect(message.parts[2]?.type === "text" && message.parts[2].text).toBe("下文确认。");
  });
});
