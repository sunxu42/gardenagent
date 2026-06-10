import { useCallback, useEffect, useRef, useState } from "react";
import {
  AFFECT_GUIDE_MOTION_EASE_CSS,
  AFFECT_GUIDE_MOTION_MS,
} from "../../lib/affectGuideMotion";

export interface GuideNavItem {
  id: string;
  label: string;
}

interface AffectGuideNavProps {
  items: readonly GuideNavItem[];
  activeId: string;
  onSelect: (id: string) => void;
}

export function AffectGuideNav({ items, activeId, onSelect }: AffectGuideNavProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef(new Map<string, HTMLButtonElement>());
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  const measureIndicator = useCallback((id: string) => {
    const track = trackRef.current;
    const tab = tabRefs.current.get(id);
    if (!track || !tab) return;
    const trackRect = track.getBoundingClientRect();
    const tabRect = tab.getBoundingClientRect();
    setIndicator({
      left: tabRect.left - trackRect.left,
      width: tabRect.width,
    });
  }, []);

  useEffect(() => {
    measureIndicator(activeId);
  }, [activeId, measureIndicator, items]);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const ro = new ResizeObserver(() => measureIndicator(activeId));
    ro.observe(track);
    return () => ro.disconnect();
  }, [activeId, measureIndicator]);

  return (
    <nav
      className="affect-guide-nav shrink-0 border-b border-border/30 px-4 pb-3 pt-2"
      aria-label="说明分区导航"
    >
      <div
        ref={trackRef}
        className="relative flex rounded-lg border border-border/40 bg-muted/20"
        role="tablist"
      >
        <div
          className="affect-guide-nav-indicator pointer-events-none absolute top-0.5 bottom-0.5 rounded-[5px] bg-primary/25 shadow-sm"
          style={{
            width: indicator.width,
            transform: `translateX(${indicator.left}px)`,
            transition: `transform ${AFFECT_GUIDE_MOTION_MS}ms ${AFFECT_GUIDE_MOTION_EASE_CSS}, width ${AFFECT_GUIDE_MOTION_MS}ms ${AFFECT_GUIDE_MOTION_EASE_CSS}`,
          }}
          aria-hidden
        />
        {items.map((item, i) => {
          const selected = activeId === item.id;
          return (
            <button
              key={item.id}
              ref={(el) => {
                if (el) tabRefs.current.set(item.id, el);
                else tabRefs.current.delete(item.id);
              }}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-current={selected ? "true" : undefined}
              onClick={() => onSelect(item.id)}
              className={`relative z-[1] flex min-w-0 flex-1 cursor-pointer items-center justify-center gap-1 whitespace-nowrap rounded-md px-1.5 py-1.5 text-[10px] font-medium transition-colors duration-200 ${selected ? "text-primary" : "text-muted-foreground hover:text-foreground"
                }`}
            >
              <span className="shrink-0 tabular-nums font-semibold">{i + 1}</span>
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
