import type { ChatMessage } from "../types";

/** 将消息按「用户开口 → 后续助手回复」划分为轮次（保持输入顺序）。 */
export function groupMessagesIntoRounds(messages: readonly ChatMessage[]): ChatMessage[][] {
  const rounds: ChatMessage[][] = [];
  let current: ChatMessage[] = [];

  for (const message of messages) {
    if (message.role === "user") {
      if (current.length > 0) {
        rounds.push(current);
      }
      current = [message];
      continue;
    }
    if (current.length === 0) {
      rounds.push([message]);
      continue;
    }
    current.push(message);
  }

  if (current.length > 0) {
    rounds.push(current);
  }

  return rounds;
}

export function takeLastRounds(rounds: readonly ChatMessage[][], count: number): ChatMessage[] {
  if (count <= 0 || rounds.length === 0) {
    return [];
  }
  const slice = rounds.slice(Math.max(0, rounds.length - count));
  return slice.flat();
}

export function oldestCreatedAt(messages: readonly ChatMessage[]): number | null {
  let min: number | null = null;
  for (const message of messages) {
    const t = message.createdAt;
    if (typeof t !== "number") {
      continue;
    }
    if (min === null || t < min) {
      min = t;
    }
  }
  return min;
}

/**
 * 从更早的一批消息中，取出紧邻当前已加载内容之前的若干完整轮次（去重）。
 */
export function pickOlderRoundsToPrepend(
  olderMessagesAsc: readonly ChatMessage[],
  existingIds: ReadonlySet<string>,
  roundCount: number,
): { messages: ChatMessage[]; hasMoreInBatch: boolean } {
  const rounds = groupMessagesIntoRounds(olderMessagesAsc);
  const eligibleRounds = rounds.filter((round) => !round.some((m) => existingIds.has(m.id)));
  const prependRounds = eligibleRounds.slice(
    Math.max(0, eligibleRounds.length - roundCount),
  );

  return {
    messages: prependRounds.flat(),
    hasMoreInBatch: eligibleRounds.length > prependRounds.length,
  };
}
