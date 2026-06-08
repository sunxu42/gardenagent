import type { ChatMessage } from "../types";
import { fetchMessagesForUser, upsertChatMessages } from "./chatHistoryDb";
import { parseMessageTurnTimestamp } from "./chatMessageOrder";
import {
  CHAT_HISTORY_FETCH_BATCH,
  CHAT_HISTORY_INITIAL_ROUNDS,
  CHAT_HISTORY_PAGE_ROUNDS,
  toChatMessage,
  toStoredMessage,
  type StoredChatMessage,
} from "./chatHistoryTypes";
import { sortChatMessagesChronologically } from "./chatMessageOrder";
import { groupMessagesIntoRounds, oldestCreatedAt, pickOlderRoundsToPrepend, takeLastRounds } from "./chatRounds";

export interface LoadRecentResult {
  messages: ChatMessage[];
  hasMore: boolean;
}

export async function loadRecentChatHistory(userId: string): Promise<LoadRecentResult> {
  const stored = await fetchMessagesForUser(userId, { limit: CHAT_HISTORY_FETCH_BATCH });
  const messages = sortChatMessagesChronologically(stored.map(toChatMessage));
  const rounds = groupMessagesIntoRounds(messages);
  const visible = takeLastRounds(rounds, CHAT_HISTORY_INITIAL_ROUNDS);
  const hasMore =
    rounds.length > CHAT_HISTORY_INITIAL_ROUNDS || stored.length >= CHAT_HISTORY_FETCH_BATCH;
  return { messages: visible, hasMore };
}

export async function loadOlderChatHistory(
  userId: string,
  currentMessages: readonly ChatMessage[],
): Promise<{ messages: ChatMessage[]; hasMore: boolean }> {
  const oldest = oldestCreatedAt(currentMessages);
  if (oldest === null) {
    return { messages: [], hasMore: false };
  }

  const stored = await fetchMessagesForUser(userId, {
    beforeCreatedAt: oldest,
    limit: CHAT_HISTORY_FETCH_BATCH,
  });
  const existingIds = new Set(currentMessages.map((m) => m.id));
  const olderAsc = sortChatMessagesChronologically(stored.map(toChatMessage));
  const { messages, hasMoreInBatch } = pickOlderRoundsToPrepend(
    olderAsc,
    existingIds,
    CHAT_HISTORY_PAGE_ROUNDS,
  );

  const hasMore =
    messages.length > 0 &&
    (hasMoreInBatch || stored.length >= CHAT_HISTORY_FETCH_BATCH);

  return { messages, hasMore };
}

const createdAtByMessageId = new Map<string, number>();

export function rememberCreatedAt(messageId: string, createdAt: number): void {
  createdAtByMessageId.set(messageId, createdAt);
}

export function resolveCreatedAt(message: ChatMessage, listIndex: number, baseTime: number): number {
  const fromId = parseMessageTurnTimestamp(message.id);
  if (fromId !== null) {
    createdAtByMessageId.set(message.id, fromId);
    return fromId;
  }
  if (typeof message.createdAt === "number" && message.createdAt > 0) {
    createdAtByMessageId.set(message.id, message.createdAt);
    return message.createdAt;
  }
  const createdAt = baseTime + listIndex;
  createdAtByMessageId.set(message.id, createdAt);
  return createdAt;
}

export function buildStoredBatch(messages: readonly ChatMessage[], userId: string): StoredChatMessage[] {
  const baseTime = Date.now() - messages.length;
  const batch: StoredChatMessage[] = [];
  for (let index = 0; index < messages.length; index += 1) {
    const message = messages[index];
    const createdAt = resolveCreatedAt(message, index, baseTime);
    const stored = toStoredMessage(message, userId, createdAt);
    if (stored) {
      batch.push(stored);
    }
  }
  return batch;
}

export async function persistChatMessages(messages: readonly ChatMessage[], userId: string): Promise<void> {
  const batch = buildStoredBatch(messages, userId);
  if (batch.length === 0) {
    return;
  }
  await upsertChatMessages(batch);
}

/** 测试用：重置内存中的 createdAt 缓存 */
export function resetChatHistoryCreatedAtCache(): void {
  createdAtByMessageId.clear();
}
