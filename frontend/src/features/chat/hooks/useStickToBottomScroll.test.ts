import { describe, expect, it } from "vitest";
import {
  CHAT_SCROLL_PIN_THRESHOLD_PX,
  isChatScrollNearBottom,
  scrollChatToBottom,
} from "./useStickToBottomScroll";

function mockScrollElement(metrics: {
  scrollHeight: number;
  scrollTop: number;
  clientHeight: number;
}): HTMLElement {
  const el = document.createElement("div");
  Object.defineProperty(el, "scrollHeight", { value: metrics.scrollHeight, configurable: true });
  Object.defineProperty(el, "clientHeight", { value: metrics.clientHeight, configurable: true });
  Object.defineProperty(el, "scrollTop", {
    value: metrics.scrollTop,
    writable: true,
    configurable: true,
  });
  return el;
}

describe("isChatScrollNearBottom", () => {
  it("returns true when within threshold of bottom", () => {
    const el = mockScrollElement({ scrollHeight: 1000, scrollTop: 920, clientHeight: 80 });
    expect(isChatScrollNearBottom(el)).toBe(true);
  });

  it("returns false when scrolled up beyond threshold", () => {
    const el = mockScrollElement({ scrollHeight: 1000, scrollTop: 800, clientHeight: 80 });
    expect(isChatScrollNearBottom(el)).toBe(false);
  });

  it("uses expanded default threshold", () => {
    const el = mockScrollElement({
      scrollHeight: 1000,
      scrollTop: 1000 - 80 - 60,
      clientHeight: 80,
    });
    expect(CHAT_SCROLL_PIN_THRESHOLD_PX).toBeGreaterThanOrEqual(60);
    expect(isChatScrollNearBottom(el)).toBe(true);
  });
});

describe("scrollChatToBottom", () => {
  it("sets scrollTop to scrollHeight", () => {
    const el = mockScrollElement({ scrollHeight: 1200, scrollTop: 0, clientHeight: 400 });
    scrollChatToBottom(el);
    expect(el.scrollTop).toBe(1200);
  });
});
