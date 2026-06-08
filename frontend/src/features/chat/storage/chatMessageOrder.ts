import type { ChatMessage } from "../types";

const TURN_ID_PATTERN = /^(?:user|assistant)(?:-voice|-fallback)?-(\d+)$/;

/** 从消息 id 解析轮次发送时刻（毫秒）。 */
export function parseMessageTurnTimestamp(id: string): number | null {
  const match = TURN_ID_PATTERN.exec(id);
  if (!match) {
    return null;
  }
  const value = Number(match[1]);
  return Number.isFinite(value) ? value : null;
}

/** 将旧版 ×2 排序键还原为真实毫秒时间戳。 */
export function normalizeLegacyCreatedAt(createdAt: number, messageId: string): number {
  if (!Number.isFinite(createdAt)) {
    return createdAt;
  }
  const fromId = parseMessageTurnTimestamp(messageId);
  if (fromId !== null) {
    return fromId;
  }
  if (createdAt > 1e13) {
    return Math.floor(createdAt / 2);
  }
  return createdAt;
}

/**
 * 恢复与界面一致的顺序：先按轮次时间戳，同轮内 user 在 assistant 前，最后按 createdAt / id。
 */
export function sortChatMessagesChronologically(messages: readonly ChatMessage[]): ChatMessage[] {
  return [...messages].sort((a, b) => {
    const turnA = parseMessageTurnTimestamp(a.id);
    const turnB = parseMessageTurnTimestamp(b.id);
    if (turnA !== null && turnB !== null && turnA !== turnB) {
      return turnA - turnB;
    }
    if (turnA !== null && turnB === null) {
      return -1;
    }
    if (turnA === null && turnB !== null) {
      return 1;
    }

    const createdA = a.createdAt ?? 0;
    const createdB = b.createdAt ?? 0;
    if (createdA !== createdB) {
      return createdA - createdB;
    }

    if (a.role !== b.role) {
      return a.role === "user" ? -1 : 1;
    }

    return a.id.localeCompare(b.id);
  });
}
