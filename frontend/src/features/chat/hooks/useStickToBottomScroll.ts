import { useCallback, useEffect, useRef, type RefObject } from "react";

/** 距底部在此阈值内视为「贴在底部」，约 1～2 行文字高度。 */
export const CHAT_SCROLL_PIN_THRESHOLD_PX = 32;

export function isChatScrollNearBottom(
  element: HTMLElement,
  threshold = CHAT_SCROLL_PIN_THRESHOLD_PX,
): boolean {
  const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
  return distanceFromBottom <= threshold;
}

export function scrollChatToBottom(element: HTMLElement): void {
  element.scrollTop = element.scrollHeight;
}

/**
 * 聊天主区域贴底滚动：用户在底部附近时随新消息自动滚到底；上滑看历史时不打断。
 */
export function useStickToBottomScroll(messages: unknown): {
  scrollRef: RefObject<HTMLElement>;
  onScroll: () => void;
} {
  const scrollRef = useRef<HTMLElement>(null);
  const pinnedToBottomRef = useRef(true);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    pinnedToBottomRef.current = isChatScrollNearBottom(el);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !pinnedToBottomRef.current) {
      return;
    }
    const frame = requestAnimationFrame(() => {
      const node = scrollRef.current;
      if (node && pinnedToBottomRef.current) {
        scrollChatToBottom(node);
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [messages]);

  return { scrollRef, onScroll };
}
