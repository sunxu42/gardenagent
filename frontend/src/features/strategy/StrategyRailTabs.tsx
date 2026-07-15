import type { LucideIcon } from "lucide-react";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  AFFECT_GUIDE_MOTION_EASE_CSS,
  RAIL_TAB_MOTION_MS,
} from "@/features/chat/lib/affectGuideMotion";
import type { StrategyPanelTab, StrategyTabGroup } from "./types";

export interface StrategyRailTabConfig {
  id: StrategyPanelTab;
  icon: LucideIcon;
  label: string;
  group: StrategyTabGroup;
}

export type { StrategyTabGroup } from "./types";

interface StrategyRailTabsProps {
  tabs: readonly StrategyRailTabConfig[];
  activeTab: StrategyPanelTab;
  onTabChange: (tab: StrategyPanelTab) => void;
  onTabPrefetch?: (tab: StrategyPanelTab) => void;
}

export function StrategyRailTabs({
  tabs,
  activeTab,
  onTabChange,
  onTabPrefetch,
}: StrategyRailTabsProps) {
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
        {tabs.map((tab, index) => {
          const selected = activeTab === tab.id;
          const prevTab = index > 0 ? tabs[index - 1] : null;
          const showSeparator = prevTab !== null && prevTab.group !== tab.group;
          const { id, icon: Icon, label } = tab;
          return (
            <Fragment key={id}>
              {showSeparator ? <div className="strategy-rail-tab-sep" aria-hidden /> : null}
              <Button
                ref={(el) => {
                  if (el) tabRefs.current.set(id, el);
                  else tabRefs.current.delete(id);
                }}
                type="button"
                variant="ghost"
                role="tab"
                aria-selected={selected}
                aria-current={selected ? "page" : undefined}
                aria-label={label}
                title={label}
                onClick={() => onTabChange(id)}
                onMouseEnter={() => onTabPrefetch?.(id)}
                onFocus={() => onTabPrefetch?.(id)}
                className={`strategy-rail-tab h-auto cursor-pointer shadow-none hover:bg-transparent${selected ? " strategy-rail-tab--active" : ""}`}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden />
                <span className="strategy-rail-tab__label">{label}</span>
              </Button>
            </Fragment>
          );
        })}
      </div>
    </nav>
  );
}
