import { useCallback, useEffect, useState, type RefObject } from "react";

const SCROLL_EDGE_THRESHOLD_PX = 6;

export function useScrollEdgeFade(
  scrollRef: RefObject<HTMLElement | null>,
  active = true,
): {
  fadeTop: boolean;
  fadeBottom: boolean;
  onScroll: () => void;
} {
  const [fadeTop, setFadeTop] = useState(false);
  const [fadeBottom, setFadeBottom] = useState(false);

  const update = useCallback(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    const { scrollTop, scrollHeight, clientHeight } = el;
    setFadeTop(scrollTop > SCROLL_EDGE_THRESHOLD_PX);
    setFadeBottom(scrollTop + clientHeight < scrollHeight - SCROLL_EDGE_THRESHOLD_PX);
  }, [scrollRef]);

  useEffect(() => {
    if (!active) {
      return;
    }
    update();
    const el = scrollRef.current;
    if (!el || typeof ResizeObserver === "undefined") {
      return;
    }
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [active, update, scrollRef]);

  return { fadeTop, fadeBottom, onScroll: update };
}
