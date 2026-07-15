import { useCallback, useEffect, useRef, type RefObject } from "react";

/** 距底部在此阈值内视为「贴在底部」，需覆盖浮动 composer 与轻微弹性滚动误差。 */
export const CHAT_SCROLL_PIN_THRESHOLD_PX = 80;

/** 程序化贴底后短暂忽略 onScroll，避免键盘/布局抖动误判为「已上滑」。 */
const SCROLL_PIN_LOCK_MS = 200;

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

/** 双 rAF：等 DOM 布局稳定后再贴底，避免 A2UI / 流式文本首帧高度不足。 */
export function scrollChatToBottomAfterLayout(element: HTMLElement): void {
  requestAnimationFrame(() => {
    scrollChatToBottom(element);
    requestAnimationFrame(() => {
      scrollChatToBottom(element);
    });
  });
}

/**
 * 聊天主区域贴底滚动：用户在底部附近时随新消息自动滚到底；上滑看历史时不打断。
 */
export function useStickToBottomScroll(messages: unknown): {
  scrollRef: RefObject<HTMLElement>;
  onScroll: () => void;
  pinToBottom: () => void;
} {
  const scrollRef = useRef<HTMLElement>(null);
  const pinnedToBottomRef = useRef(true);
  const scrollLockUntilRef = useRef(0);

  const scrollIfPinned = useCallback(() => {
    const el = scrollRef.current;
    if (!el || !pinnedToBottomRef.current) {
      return;
    }
    scrollChatToBottomAfterLayout(el);
  }, []);

  const pinToBottom = useCallback(() => {
    pinnedToBottomRef.current = true;
    scrollLockUntilRef.current = performance.now() + SCROLL_PIN_LOCK_MS;
    scrollIfPinned();
  }, [scrollIfPinned]);

  const onScroll = useCallback(() => {
    if (performance.now() < scrollLockUntilRef.current) {
      pinnedToBottomRef.current = true;
      return;
    }
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    pinnedToBottomRef.current = isChatScrollNearBottom(el);
  }, []);

  useEffect(() => {
    scrollIfPinned();
  }, [messages, scrollIfPinned]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || typeof ResizeObserver === "undefined") {
      return;
    }

    const ro = new ResizeObserver(() => {
      scrollIfPinned();
    });
    ro.observe(el);
    const list = el.querySelector(".chat-message-list");
    if (list) {
      ro.observe(list);
    }

    return () => ro.disconnect();
  }, [scrollIfPinned]);

  return { scrollRef, onScroll, pinToBottom };
}
