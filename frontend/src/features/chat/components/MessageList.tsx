import { cn } from "@/lib/utils";
import type { ChatMessage } from "../types";

interface MessageListProps {
  messages: ChatMessage[];
  defaultAssistantLabel?: string;
  historyLoading?: boolean;
  hasMoreHistory?: boolean;
}

export function MessageList({
  messages,
  defaultAssistantLabel = "助手",
  historyLoading = false,
  hasMoreHistory = false,
}: MessageListProps) {
  return (
    <ul aria-label="消息列表" className="chat-message-list m-0 flex list-none flex-col gap-3 p-0">
      {hasMoreHistory ? (
        <li
          className="list-none py-1 text-center text-xs text-muted-foreground"
          aria-live="polite"
          aria-busy={historyLoading}
        >
          {historyLoading ? (
            "正在加载更早的消息…"
          ) : (
            <>
              <span className="md:hidden">向上滑动加载更早的对话</span>
              <span className="hidden md:inline">向上滚动加载更早的对话</span>
            </>
          )}
        </li>
      ) : null}
      {messages.map((message) => (
        <li
          key={message.id}
          className={cn(
            `msg-bubble--${message.role} w-fit max-w-[90%] rounded-xl border px-3 py-2.5 shadow-sm`,
            message.role === "user"
              ? "self-end bg-primary text-primary-foreground"
              : "self-start bg-muted",
          )}
          data-streaming={message.status === "streaming"}
        >
          <strong className="msg-author text-sm font-semibold">
            {message.role === "user" ? "我" : message.authorLabel ?? defaultAssistantLabel}：
          </strong>
          <span className="msg-text whitespace-pre-wrap break-words">
            {message.content || "..."}
          </span>
        </li>
      ))}
    </ul>
  );
}
