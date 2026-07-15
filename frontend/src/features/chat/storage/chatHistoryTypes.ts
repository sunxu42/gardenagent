import type { ChatMessage, MessagePart, MessageRole } from "../types";
import { getMessageText, textPart } from "../lib/messageParts";

export const CHAT_HISTORY_DB_NAME = "gardenagent.chat.history.v1";
export const CHAT_HISTORY_STORE = "messages";
export const CHAT_HISTORY_INDEX_USER_TIME = "by_user_time";

/** 首次进入界面展示的最近对话轮数 */
export const CHAT_HISTORY_INITIAL_ROUNDS = 10;
/** 上滑每次追加加载的轮数 */
export const CHAT_HISTORY_PAGE_ROUNDS = 10;
/** 单次从 IndexedDB 拉取的消息条数上限（用于分组为轮次） */
export const CHAT_HISTORY_FETCH_BATCH = 400;

export interface StoredChatMessage {
  id: string;
  userId: string;
  role: MessageRole;
  content: string;
  parts?: MessagePart[];
  authorLabel?: string;
  /** AG-UI run id — restored so pending A2UI cards stay interactive after reload */
  runId?: string;
  createdAt: number;
}

export function messagePersistFingerprint(message: ChatMessage): string {
  const textLength = getMessageText(message).trim().length;
  const a2uiSignature = message.parts
    .filter((part) => part.type === "a2ui")
    .map((part) => `${part.surfaceId}:${part.status}:${part.interaction ?? ""}:${part.messages.length}`)
    .join(",");
  return `${message.id}:${message.status}:${textLength}:${message.runId ?? ""}:${a2uiSignature}`;
}

export function toStoredMessage(message: ChatMessage, userId: string, createdAt: number): StoredChatMessage | null {
  const content = getMessageText(message).trim();
  const hasA2uiPart = message.parts.some((part) => part.type === "a2ui");
  if (!content && !hasA2uiPart) {
    return null;
  }
  // Interactive A2UI cards stay streaming until the user acts; still persist them.
  if (message.role === "assistant" && message.status !== "done" && !hasA2uiPart) {
    return null;
  }
  return {
    id: message.id,
    userId,
    role: message.role,
    content,
    parts: message.parts,
    ...(message.authorLabel ? { authorLabel: message.authorLabel } : {}),
    ...(message.runId ? { runId: message.runId } : {}),
    createdAt,
  };
}

export function toChatMessage(stored: StoredChatMessage): ChatMessage {
  const parts =
    stored.parts && stored.parts.length > 0
      ? stored.parts
      : stored.content
        ? [textPart(stored.content)]
        : [textPart("")];
  const hasPendingA2ui = parts.some(
    (part) => part.type === "a2ui" && part.interaction === "pending",
  );
  return {
    id: stored.id,
    role: stored.role,
    parts,
    content: stored.content,
    status: hasPendingA2ui ? "streaming" : "done",
    ...(stored.authorLabel ? { authorLabel: stored.authorLabel } : {}),
    ...(stored.runId ? { runId: stored.runId } : {}),
    createdAt: stored.createdAt,
  };
}
