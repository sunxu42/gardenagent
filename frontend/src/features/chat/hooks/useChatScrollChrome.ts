import { useCallback, useState, type RefObject } from "react";

const COMPACT_SCROLL_THRESHOLD_PX = 20;

/**
 * Tracks chat scroll position to compact floating Liquid Glass chrome (iOS 26 tab-bar shrink).
 */
export function useChatScrollChrome(scrollRef: RefObject<HTMLElement | null>): {
  compact: boolean;
  onScroll: () => void;
} {
  const [compact, setCompact] = useState(false);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    const next = el.scrollTop > COMPACT_SCROLL_THRESHOLD_PX;
    setCompact((prev) => (prev === next ? prev : next));
  }, [scrollRef]);

  return { compact, onScroll };
}
