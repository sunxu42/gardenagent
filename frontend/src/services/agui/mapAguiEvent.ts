import type { ChatAction, ChatMessage } from "../../features/chat/types";

export const AGUI_CHANNEL = "agui";

export type AguiEventType =
  | "RUN_STARTED"
  | "TEXT_MESSAGE_CONTENT"
  | "RUN_FINISHED"
  | "RUN_ERROR"
  | "A2UI_OPERATIONS";

export interface AguiEventBase {
  type: AguiEventType;
  messageId: string;
  runId: string;
}

export interface AguiTextContentEvent extends AguiEventBase {
  type: "TEXT_MESSAGE_CONTENT";
  delta: string;
}

export interface AguiRunErrorEvent extends AguiEventBase {
  type: "RUN_ERROR";
  message: string;
}

export interface AguiA2uiOperationsEvent extends AguiEventBase {
  type: "A2UI_OPERATIONS";
  surfaceId: string;
  operations: Record<string, unknown>[];
}

export type AguiEvent =
  | AguiEventBase
  | AguiTextContentEvent
  | AguiRunErrorEvent
  | AguiA2uiOperationsEvent;

export interface AguiEnvelope {
  channel: typeof AGUI_CHANNEL;
  event: AguiEvent;
}

function readAguiEvent(raw: unknown): AguiEvent | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }
  const event = raw as Record<string, unknown>;
  const type = event.type;
  const messageId = typeof event.messageId === "string" ? event.messageId : "";
  const runId = typeof event.runId === "string" ? event.runId : "";
  if (!type || !messageId || !runId) {
    return null;
  }
  if (type === "TEXT_MESSAGE_CONTENT") {
    return {
      type,
      messageId,
      runId,
      delta: typeof event.delta === "string" ? event.delta : "",
    };
  }
  if (type === "RUN_ERROR") {
    return {
      type,
      messageId,
      runId,
      message: typeof event.message === "string" ? event.message : "未知错误",
    };
  }
  if (type === "A2UI_OPERATIONS") {
    const surfaceId = typeof event.surfaceId === "string" ? event.surfaceId : "";
    const operations = Array.isArray(event.operations)
      ? event.operations.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
      : [];
    if (!surfaceId) {
      return null;
    }
    return {
      type,
      messageId,
      runId,
      surfaceId,
      operations,
    };
  }
  if (type === "RUN_STARTED" || type === "RUN_FINISHED") {
    return { type, messageId, runId };
  }
  return null;
}

export function parseAguiEnvelope(raw: Record<string, unknown>): AguiEvent | null {
  if (raw.channel !== AGUI_CHANNEL) {
    return null;
  }
  return readAguiEvent(raw.event);
}

function matchesRun(message: ChatMessage, runId: string): boolean {
  if (!message.runId) {
    return true;
  }
  return message.runId === runId;
}

export function mapAguiEvent(
  event: AguiEvent,
  assistantMessageId: string | null,
  agentName?: string,
): ChatAction | null {
  if (assistantMessageId && event.messageId !== assistantMessageId) {
    console.warn("[agui] messageId mismatch, dropping event", event.type);
    return null;
  }

  if (event.type === "RUN_STARTED") {
    return {
      type: "aguiRunStarted",
      payload: {
        messageId: event.messageId,
        runId: event.runId,
        ...(agentName ? { agentName } : {}),
      },
    };
  }

  if (event.type === "TEXT_MESSAGE_CONTENT") {
    const textEvent = event as AguiTextContentEvent;
    return {
      type: "aguiTextDelta",
      payload: {
        messageId: textEvent.messageId,
        runId: textEvent.runId,
        delta: textEvent.delta,
        ...(agentName ? { agentName } : {}),
      },
    };
  }

  if (event.type === "RUN_FINISHED") {
    return {
      type: "aguiRunFinished",
      payload: { messageId: event.messageId, runId: event.runId },
    };
  }

  if (event.type === "A2UI_OPERATIONS") {
    const a2uiEvent = event as AguiA2uiOperationsEvent;
    return {
      type: "aguiA2uiOps",
      payload: {
        messageId: a2uiEvent.messageId,
        runId: a2uiEvent.runId,
        surfaceId: a2uiEvent.surfaceId,
        operations: a2uiEvent.operations,
      },
    };
  }

  if (event.type === "RUN_ERROR") {
    const errorEvent = event as AguiRunErrorEvent;
    return {
      type: "aguiRunError",
      payload: {
        messageId: errorEvent.messageId,
        runId: errorEvent.runId,
        message: errorEvent.message,
      },
    };
  }

  return null;
}

export function applyAguiRunGuard(
  message: ChatMessage,
  runId: string,
  actionType: string,
): boolean {
  if (!matchesRun(message, runId)) {
    console.warn(`[agui] runId mismatch on ${actionType}, dropping event`);
    return false;
  }
  return true;
}
