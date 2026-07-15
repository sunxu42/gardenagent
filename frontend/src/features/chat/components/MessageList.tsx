import { cn } from "@/lib/utils";
import type { ChatMessage } from "../types";
import { hasVisibleMessageContent, isAssistantThinking } from "../lib/messageParts";
import { A2UISurface } from "./A2UISurface";
import { AssistantThinkingIndicator } from "./AssistantThinkingIndicator";

interface MessageListProps {
  messages: ChatMessage[];
  historyLoading?: boolean;
  hasMoreHistory?: boolean;
  connectionStatus?: "online" | "offline";
  onUiAction?: (payload: {
    runId: string;
    messageId: string;
    surfaceId: string;
    action: {
      name: string;
      context?: Record<string, unknown>;
      sourceComponentId?: string;
      dataModel?: Record<string, unknown>;
    };
  }) => void;
}

export function MessageList({
  messages,
  historyLoading = false,
  hasMoreHistory = false,
  connectionStatus = "online",
  onUiAction,
}: MessageListProps) {
  return (
    <ul aria-label="消息列表" className="chat-message-list m-0 flex list-none flex-col p-0">
      {hasMoreHistory ? (
        <li
          className="list-none py-1 text-center"
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
      {messages.map((message) => {
        const thinking = isAssistantThinking(message);
        const streaming =
          message.role === "assistant" &&
          (message.status === "streaming" || message.status === "sending");

        return (
          <li
            key={message.id}
            className={cn(
              `msg-bubble--${message.role}`,
              message.role === "user"
                ? "w-fit self-end"
                : thinking
                  ? "w-fit self-start"
                  : "w-full self-start",
            )}
            data-thinking={thinking || undefined}
            data-streaming={streaming && !thinking ? true : undefined}
          >
            <div className="msg-text space-y-2 whitespace-pre-wrap break-words">
              {thinking ? (
                <AssistantThinkingIndicator />
              ) : (
                <>
                  {message.parts.map((part, index) => {
                    if (part.type === "text") {
                      if (!part.text) {
                        return null;
                      }
                      return <span key={`${message.id}-text-${index}`}>{part.text}</span>;
                    }
                    return (
                      <A2UISurface
                        key={`${message.id}-a2ui-${part.surfaceId}-${index}`}
                        part={part}
                        message={message}
                        connectionOnline={connectionStatus === "online"}
                        onAction={(action) => {
                          if (connectionStatus !== "online" || !message.runId || !onUiAction) {
                            return;
                          }
                          onUiAction({
                            runId: message.runId,
                            messageId: message.id,
                            surfaceId: part.surfaceId,
                            action,
                          });
                        }}
                      />
                    );
                  })}
                  {streaming && hasVisibleMessageContent(message) ? (
                    <span className="ios-stream-cursor" aria-hidden="true" />
                  ) : null}
                </>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
