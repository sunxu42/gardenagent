import { useLayoutEffect, type RefObject } from "react";

export const CHAT_COMPOSER_MAX_ROWS = 4;

/**
 * 输入框随内容增高，最多 {@link CHAT_COMPOSER_MAX_ROWS} 行；超出后纵向滚动，不换行出横向滚动条。
 */
export function useAutosizeChatTextarea(
  ref: RefObject<HTMLTextAreaElement | null>,
  value: string,
): void {
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) {
      return;
    }

    element.style.height = "0px";
    const style = getComputedStyle(element);
    const lineHeight = Number.parseFloat(style.lineHeight) || 20;
    const paddingY =
      Number.parseFloat(style.paddingTop) + Number.parseFloat(style.paddingBottom);
    const borderY =
      Number.parseFloat(style.borderTopWidth) + Number.parseFloat(style.borderBottomWidth);
    const maxHeight = lineHeight * CHAT_COMPOSER_MAX_ROWS + paddingY + borderY;
    const contentHeight = element.scrollHeight;
    const nextHeight = Math.min(contentHeight, maxHeight);

    element.style.height = `${nextHeight}px`;
    element.style.overflowY = contentHeight > maxHeight ? "auto" : "hidden";
    element.style.overflowX = "hidden";
  }, [ref, value]);
}
