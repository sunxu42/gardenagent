import type { ReactNode } from "react";

interface A2UIChatBubblePreviewProps {
  /** Optional user utterance shown above the assistant bubble. */
  userPreviewText?: string;
  children: ReactNode;
}

/**
 * Renders A2UI inside the same DOM/CSS context as MessageList assistant bubbles.
 */
export function A2UIChatBubblePreview({
  userPreviewText,
  children,
}: A2UIChatBubblePreviewProps) {
  return (
    <div className="a2ui-panel-preview">
      <div className="a2ui-panel-preview__label">聊天预览 · iPhone 17 Pro Max (440pt)</div>
      <div className="a2ui-panel-preview__frame">
        <div className="a2ui-panel-preview__canvas chat-ios">
          <ul
            aria-label="A2UI 聊天预览"
            className="chat-message-list m-0 flex list-none flex-col p-0"
          >
            {userPreviewText ? (
              <li className="msg-bubble--user w-fit self-end">
                <div className="msg-text whitespace-pre-wrap break-words">{userPreviewText}</div>
              </li>
            ) : null}
            <li className="msg-bubble--assistant w-full self-start">
              <div className="msg-text space-y-2 whitespace-pre-wrap break-words">{children}</div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
