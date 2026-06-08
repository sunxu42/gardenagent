import type { ChatMessage, MessageRole } from "../types";

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
  authorLabel?: string;
  createdAt: number;
}

export function toStoredMessage(message: ChatMessage, userId: string, createdAt: number): StoredChatMessage | null {
  const content = message.content.trim();
  if (!content) {
    return null;
  }
  if (message.role === "assistant" && message.status !== "done") {
    return null;
  }
  return {
    id: message.id,
    userId,
    role: message.role,
    content,
    ...(message.authorLabel ? { authorLabel: message.authorLabel } : {}),
    createdAt,
  };
}

export function toChatMessage(stored: StoredChatMessage): ChatMessage {
  return {
    id: stored.id,
    role: stored.role,
    content: stored.content,
    status: "done",
    ...(stored.authorLabel ? { authorLabel: stored.authorLabel } : {}),
    createdAt: stored.createdAt,
  };
}
