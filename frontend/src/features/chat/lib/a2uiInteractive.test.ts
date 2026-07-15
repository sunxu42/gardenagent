import { describe, expect, it } from "vitest";
import {
  a2uiInteractionLabel,
  isA2uiPartInteractable,
  isInteractiveA2uiSurface,
} from "./a2uiInteractive";
import type { A2uiPart, ChatMessage } from "../types";

const baseMessage: ChatMessage = {
  id: "assistant-1",
  role: "assistant",
  parts: [],
  content: "",
  status: "streaming",
  runId: "run-1",
};

const pendingPart: A2uiPart = {
  type: "a2ui",
  surfaceId: "single-select-cards",
  status: "ready",
  messages: [],
  interaction: "pending",
};

describe("a2uiInteractive", () => {
  it("marks single-select surfaces as interactive", () => {
    expect(isInteractiveA2uiSurface("single-select")).toBe(true);
    expect(isInteractiveA2uiSurface("single-select-binary")).toBe(true);
    expect(isInteractiveA2uiSurface("single-select-emoji")).toBe(true);
    expect(isInteractiveA2uiSurface("single-select-cards")).toBe(true);
    expect(isInteractiveA2uiSurface("multi-select")).toBe(true);
    expect(isInteractiveA2uiSurface("date-picker")).toBe(true);
    expect(isInteractiveA2uiSurface("data-table-select")).toBe(true);
    expect(isInteractiveA2uiSurface("plan-selector")).toBe(true);
    expect(isInteractiveA2uiSurface("info-card")).toBe(false);
    expect(isInteractiveA2uiSurface("data-table")).toBe(false);
  });

  it("keeps pending surfaces clickable after message is done", () => {
    const doneMessage = { ...baseMessage, status: "done" as const };
    expect(isA2uiPartInteractable(pendingPart, doneMessage, true)).toBe(true);
    expect(a2uiInteractionLabel(pendingPart, doneMessage, true)).toBe("方案选择 · 可交互");
  });

  it("disables resolved surfaces", () => {
    const resolvedPart: A2uiPart = { ...pendingPart, interaction: "resolved" };
    expect(isA2uiPartInteractable(resolvedPart, baseMessage, true)).toBe(false);
    expect(a2uiInteractionLabel(resolvedPart, baseMessage, true)).toBe("方案选择 · 已选择");
  });
});
