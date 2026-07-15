import type { ChatMessage, MessagePart, MessageRole, MessageStatus, TextPart } from "../types";

export function textPart(text: string): TextPart {
  return { type: "text", text };
}

export function emptyTextParts(): MessagePart[] {
  return [textPart("")];
}

export function hasVisibleMessageContent(message: Pick<ChatMessage, "parts">): boolean {
  return message.parts.some((part) => {
    if (part.type === "text") {
      return part.text.trim().length > 0;
    }
    return part.messages.length > 0;
  });
}

export function isAssistantThinking(message: ChatMessage): boolean {
  return (
    message.role === "assistant" &&
    (message.status === "sending" || message.status === "streaming") &&
    !hasVisibleMessageContent(message)
  );
}

export function getMessageText(message: Pick<ChatMessage, "parts" | "content">): string {
  if (message.parts.length > 0) {
    return message.parts
      .filter((part): part is TextPart => part.type === "text")
      .map((part) => part.text)
      .join("");
  }
  return message.content;
}

export function syncMessageContent(message: ChatMessage): ChatMessage {
  const content = getMessageText(message);
  return { ...message, content };
}

export function appendTextDelta(message: ChatMessage, delta: string): ChatMessage {
  const parts = [...message.parts];
  const last = parts[parts.length - 1];
  if (last?.type === "text") {
    parts[parts.length - 1] = textPart(last.text + delta);
  } else {
    parts.push(textPart(delta));
  }
  return syncMessageContent({ ...message, parts });
}

export function createMessageFromText(
  id: string,
  role: MessageRole,
  content: string,
  status: MessageStatus = "sending",
): ChatMessage {
  return syncMessageContent({
    id,
    role,
    parts: [textPart(content)],
    content,
    status,
  });
}
