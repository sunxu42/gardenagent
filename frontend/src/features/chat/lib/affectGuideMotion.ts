/** 说明栏导航滑块 + 内容区滚动 */
export const AFFECT_GUIDE_MOTION_MS = 480;

/** 策略侧栏 tab（内容切换无动画，滑块略快） */
export const RAIL_TAB_MOTION_MS = 280;

export const AFFECT_GUIDE_MOTION_EASE_CSS = "cubic-bezier(0.4, 0, 0.2, 1)";

/** Material standard ease-out，与上方 cubic-bezier 视觉一致 */
export function affectGuideEase(t: number): number {
  const x = Math.max(0, Math.min(1, t));
  return 1 - (1 - x) ** 3;
}

export function smoothScrollContainer(
  container: HTMLElement,
  targetTop: number,
  durationMs: number = AFFECT_GUIDE_MOTION_MS,
): void {
  const startTop = container.scrollTop;
  const delta = targetTop - startTop;
  if (Math.abs(delta) < 1) return;

  const start = performance.now();

  const tick = (now: number) => {
    const elapsed = now - start;
    const progress = Math.min(elapsed / durationMs, 1);
    container.scrollTop = startTop + delta * affectGuideEase(progress);
    if (progress < 1) {
      requestAnimationFrame(tick);
    }
  };

  requestAnimationFrame(tick);
}

export function captureFlipPositions(container: HTMLElement): Map<string, DOMRect> {
  const map = new Map<string, DOMRect>();
  container.querySelectorAll<HTMLElement>("[data-flip-id]").forEach((el) => {
    const id = el.dataset.flipId;
    if (id) {
      map.set(id, el.getBoundingClientRect());
    }
  });
  return map;
}

export function runFlipAnimation(
  container: HTMLElement,
  firstPositions: Map<string, DOMRect>,
  durationMs: number = AFFECT_GUIDE_MOTION_MS,
): void {
  if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  container.querySelectorAll<HTMLElement>("[data-flip-id]").forEach((el) => {
    const id = el.dataset.flipId;
    if (!id) {
      return;
    }
    const first = firstPositions.get(id);
    if (!first) {
      return;
    }
    const last = el.getBoundingClientRect();
    const dy = first.top - last.top;
    const dx = first.left - last.left;
    if (Math.abs(dy) < 0.5 && Math.abs(dx) < 0.5) {
      return;
    }

    el.animate(
      [
        { transform: `translate(${dx}px, ${dy}px)` },
        { transform: "translate(0, 0)" },
      ],
      { duration: durationMs, easing: AFFECT_GUIDE_MOTION_EASE_CSS },
    );
  });
}
