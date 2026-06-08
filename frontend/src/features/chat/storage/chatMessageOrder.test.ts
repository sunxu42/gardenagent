import { describe, expect, it } from "vitest";
import {
  normalizeLegacyCreatedAt,
  parseMessageTurnTimestamp,
  sortChatMessagesChronologically,
} from "./chatMessageOrder";
import { resolveCreatedAt } from "./chatHistoryService";
import type { ChatMessage } from "../types";

describe("parseMessageTurnTimestamp", () => {
  it("parses text and voice message ids", () => {
    expect(parseMessageTurnTimestamp("user-1780639904023")).toBe(1780639904023);
    expect(parseMessageTurnTimestamp("assistant-1780639904023")).toBe(1780639904023);
    expect(parseMessageTurnTimestamp("user-voice-1780639904023")).toBe(1780639904023);
    expect(parseMessageTurnTimestamp("assistant-fallback-1780639904023")).toBe(1780639904023);
  });
});

describe("normalizeLegacyCreatedAt", () => {
  it("restores legacy ×2 timestamps", () => {
    expect(normalizeLegacyCreatedAt(3561279808046, "user-1780639904023")).toBe(1780639904023);
  });

  it("keeps normal millisecond timestamps", () => {
    expect(normalizeLegacyCreatedAt(1780639904023, "user-voice-1780639904023")).toBe(1780639904023);
  });
});

describe("resolveCreatedAt", () => {
  it("stores real milliseconds instead of ×2 sort keys", () => {
    const message: ChatMessage = {
      id: "user-1780639904023",
      role: "user",
      content: "hello",
      status: "done",
    };
    expect(resolveCreatedAt(message, 0, 1000)).toBe(1780639904023);
  });
});

describe("sortChatMessagesChronologically", () => {
  it("orders mixed text and voice rounds by turn timestamp", () => {
    const messages: ChatMessage[] = [
      {
        id: "user-voice-2000",
        role: "user",
        content: "voice",
        status: "done",
        createdAt: 2000,
      },
      {
        id: "user-1000",
        role: "user",
        content: "text",
        status: "done",
        createdAt: 1000,
      },
    ];
    const sorted = sortChatMessagesChronologically(messages);
    expect(sorted.map((m) => m.id)).toEqual(["user-1000", "user-voice-2000"]);
  });
});
