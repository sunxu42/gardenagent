import { describe, expect, it } from "vitest";
import { messagePersistFingerprint, toChatMessage, toStoredMessage } from "./chatHistoryTypes";

describe("chatHistoryTypes parts", () => {
  it("stores and restores parts", () => {
    const stored = toStoredMessage(
      {
        id: "m1",
        role: "assistant",
        parts: [{ type: "text", text: "hello" }],
        content: "hello",
        status: "done",
      },
      "user-1",
      1000,
    );
    expect(stored?.parts).toEqual([{ type: "text", text: "hello" }]);

    const restored = toChatMessage({
      id: "m1",
      userId: "user-1",
      role: "assistant",
      content: "hello",
      parts: [{ type: "text", text: "hello" }],
      createdAt: 1000,
    });
    const firstPart = restored.parts[0];
    expect(firstPart?.type).toBe("text");
    if (firstPart?.type === "text") {
      expect(firstPart.text).toBe("hello");
    }
  });

  it("stores assistant message with only a2ui parts", () => {
    const stored = toStoredMessage(
      {
        id: "m-a2ui",
        role: "assistant",
        parts: [
          {
            type: "a2ui",
            surfaceId: "plan-selector",
            status: "ready",
            messages: [
              {
                version: "v0.9",
                createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
              },
            ],
          },
        ],
        content: "",
        status: "done",
        runId: "run-1",
      },
      "user-1",
      3000,
    );
    expect(stored?.parts?.some((part) => part.type === "a2ui")).toBe(true);
    expect(stored?.runId).toBe("run-1");
  });

  it("stores streaming assistant with pending a2ui before run finishes", () => {
    const stored = toStoredMessage(
      {
        id: "m-pending",
        role: "assistant",
        parts: [
          { type: "text", text: "" },
          {
            type: "a2ui",
            surfaceId: "plan-selector",
            status: "ready",
            interaction: "pending",
            messages: [
              {
                version: "v0.9",
                createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
              },
            ],
          },
        ],
        content: "",
        status: "streaming",
        runId: "run-pending",
      },
      "user-1",
      4000,
    );
    expect(stored?.parts?.some((part) => part.type === "a2ui")).toBe(true);
    expect(stored?.runId).toBe("run-pending");
  });

  it("skips streaming assistant without a2ui parts", () => {
    const stored = toStoredMessage(
      {
        id: "m-stream",
        role: "assistant",
        parts: [{ type: "text", text: "生成中…" }],
        content: "生成中…",
        status: "streaming",
      },
      "user-1",
      5000,
    );
    expect(stored).toBeNull();
  });

  it("restores runId and streaming status for pending a2ui", () => {
    const restored = toChatMessage({
      id: "m-pending",
      userId: "user-1",
      role: "assistant",
      content: "",
      runId: "run-pending",
      parts: [
        {
          type: "a2ui",
          surfaceId: "plan-selector",
          status: "ready",
          interaction: "pending",
          messages: [
            {
              version: "v0.9",
              createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
            },
          ],
        },
      ],
      createdAt: 4000,
    });
    expect(restored.runId).toBe("run-pending");
    expect(restored.status).toBe("streaming");
  });

  it("restores done status when a2ui interaction is resolved", () => {
    const restored = toChatMessage({
      id: "m-resolved",
      userId: "user-1",
      role: "assistant",
      content: "",
      runId: "run-1",
      parts: [
        {
          type: "a2ui",
          surfaceId: "plan-selector",
          status: "ready",
          interaction: "resolved",
          messages: [
            {
              version: "v0.9",
              updateDataModel: { surfaceId: "plan-selector", path: "/selectedPlan", value: null },
            },
            {
              version: "v0.9",
              updateDataModel: { surfaceId: "plan-selector", path: "/selectedPlan", value: "plan-a" },
            },
          ],
        },
      ],
      createdAt: 5000,
    });
    expect(restored.status).toBe("done");
    const a2uiPart = restored.parts.find((part) => part.type === "a2ui");
    expect(a2uiPart?.type).toBe("a2ui");
    if (a2uiPart?.type === "a2ui") {
      const lastOp = a2uiPart.messages[a2uiPart.messages.length - 1];
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

  it("builds persist fingerprint from a2ui parts", () => {
    const fingerprint = messagePersistFingerprint({
      id: "m-a2ui",
      role: "assistant",
      parts: [
        {
          type: "a2ui",
          surfaceId: "plan-selector",
          status: "ready",
          messages: [{ version: "v0.9", createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" } }],
        },
      ],
      content: "",
      status: "done",
    });
    expect(fingerprint).toContain("plan-selector:ready::1");
  });

  it("migrates legacy content-only records", () => {
    const restored = toChatMessage({
      id: "m2",
      userId: "user-1",
      role: "user",
      content: "legacy",
      createdAt: 2000,
    });
    expect(restored.parts).toEqual([{ type: "text", text: "legacy" }]);
    expect(restored.content).toBe("legacy");
  });
});
