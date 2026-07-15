import { useLayoutEffect, type RefObject } from "react";

const FOOTER_INSET_VAR = "--chat-footer-inset";

/**
 * 测量浮动 footer 实际高度，写入 `.chat-ios` 的 CSS 变量，避免消息被 composer 遮挡。
 */
export function useChatFooterInset(
  footerRef: RefObject<HTMLElement | null>,
  scrollRef: RefObject<HTMLElement | null>,
): void {
  useLayoutEffect(() => {
    const footer = footerRef.current;
    const scrollEl = scrollRef.current;
    const shell = scrollEl?.closest(".chat-ios");
    if (!(footer && shell instanceof HTMLElement)) {
      return;
    }

    const syncInset = () => {
      const height = Math.ceil(footer.getBoundingClientRect().height);
      shell.style.setProperty(FOOTER_INSET_VAR, `${height}px`);
    };

    syncInset();

    if (typeof ResizeObserver === "undefined") {
      return;
    }

    const ro = new ResizeObserver(syncInset);
    ro.observe(footer);
    return () => ro.disconnect();
  }, [footerRef, scrollRef]);
}
