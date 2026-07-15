import type { A2uiPart, ChatMessage, MessagePart } from "../types";

export const INTERACTIVE_A2UI_SURFACE_IDS = new Set([
  "single-select",
  "single-select-binary",
  "single-select-emoji",
  "single-select-cards",
  "multi-select",
  "date-picker",
  "data-table-select",
  // Legacy surfaces for stored history.
  "plan-selector",
  "binary-choice",
  "emoji-picker",
]);

const SURFACE_KIND_LABELS: Record<string, string> = {
  "single-select": "单选",
  "single-select-binary": "二选一",
  "single-select-emoji": "表情选择",
  "single-select-cards": "方案选择",
  "multi-select": "多选",
  "date-picker": "日期选择",
  "data-table": "表格",
  "data-table-select": "表格选择",
  "plan-selector": "方案选择",
  "binary-choice": "二选一",
  "emoji-picker": "表情选择",
};

export function isInteractiveA2uiSurface(surfaceId: string): boolean {
  return INTERACTIVE_A2UI_SURFACE_IDS.has(surfaceId);
}

export function a2uiSurfaceKindLabel(surfaceId: string): string {
  return SURFACE_KIND_LABELS[surfaceId] ?? "交互卡片";
}

export function messageHasPendingA2ui(parts: MessagePart[]): boolean {
  return parts.some((part) => part.type === "a2ui" && part.interaction === "pending");
}

export function isA2uiPartInteractable(
  part: A2uiPart,
  message: ChatMessage,
  connectionOnline: boolean,
): boolean {
  if (!connectionOnline) {
    return false;
  }
  if (part.interaction === "pending") {
    return true;
  }
  if (part.interaction === "resolved") {
    return false;
  }
  return message.status === "streaming";
}

export function a2uiInteractionLabel(
  part: A2uiPart,
  message: ChatMessage,
  connectionOnline: boolean,
): string {
  const kind = a2uiSurfaceKindLabel(part.surfaceId);
  if (part.interaction === "pending") {
    return connectionOnline ? `${kind} · 可交互` : `${kind} · 离线`;
  }
  if (part.interaction === "resolved") {
    return `${kind} · 已选择`;
  }
  if (message.status === "done") {
    return `${kind} · 已结束`;
  }
  return connectionOnline ? `${kind} · 可交互` : `${kind} · 离线`;
}
