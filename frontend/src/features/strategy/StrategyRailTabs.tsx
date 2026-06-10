import type { LucideIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  AFFECT_GUIDE_MOTION_EASE_CSS,
  RAIL_TAB_MOTION_MS,
} from "@/features/chat/lib/affectGuideMotion";
import type { StrategyPanelTab } from "./types";

export interface StrategyRailTabConfig {
  id: StrategyPanelTab;
  icon: LucideIcon;
  label: string;
}

interface StrategyRailTabsProps {
  tabs: readonly StrategyRailTabConfig[];
  activeTab: StrategyPanelTab;
  onTabChange: (tab: StrategyPanelTab) => void;
}

export function StrategyRailTabs({ tabs, activeTab, onTabChange }: StrategyRailTabsProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef(new Map<string, HTMLButtonElement>());
  const [indicator, setIndicator] = useState({ top: 0, height: 0 });

  const measureIndicator = useCallback((id: string) => {
    const track = trackRef.current;
    const tab = tabRefs.current.get(id);
    if (!track || !tab) return;
    const trackRect = track.getBoundingClientRect();
    const tabRect = tab.getBoundingClientRect();
    setIndicator({
      top: tabRect.top - trackRect.top,
      height: tabRect.height,
    });
  }, []);

  useEffect(() => {
    measureIndicator(activeTab);
  }, [activeTab, measureIndicator, tabs]);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const ro = new ResizeObserver(() => measureIndicator(activeTab));
    ro.observe(track);
    return () => ro.disconnect();
  }, [activeTab, measureIndicator]);

  return (
    <nav className="strategy-rail-tabs" aria-label="策略分区">
      <div ref={trackRef} className="strategy-rail-tabs-track" role="tablist">
        <div
          className="strategy-rail-tab-indicator"
          style={{
            height: indicator.height,
            transform: `translateY(${indicator.top}px)`,
            transition: `transform ${RAIL_TAB_MOTION_MS}ms ${AFFECT_GUIDE_MOTION_EASE_CSS}, height ${RAIL_TAB_MOTION_MS}ms ${AFFECT_GUIDE_MOTION_EASE_CSS}`,
          }}
          aria-hidden
        />
        {tabs.map(({ id, icon: Icon, label }) => {
          const selected = activeTab === id;
          return (
            <button
              key={id}
              ref={(el) => {
                if (el) tabRefs.current.set(id, el);
                else tabRefs.current.delete(id);
              }}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-current={selected ? "page" : undefined}
              aria-label={label}
              title={label}
              onClick={() => onTabChange(id)}
              className={`strategy-rail-tab cursor-pointer${selected ? " strategy-rail-tab--active" : ""}`}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span className="strategy-rail-tab__label">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
