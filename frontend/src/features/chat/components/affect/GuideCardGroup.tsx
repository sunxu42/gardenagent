import type { ReactNode } from "react";

interface GuideCardGroupProps {
  accent: "amber" | "sky";
  refPanel: ReactNode;
  children: ReactNode;
}

const GROUP_CLASS: Record<GuideCardGroupProps["accent"], string> = {
  amber: "affect-guide-card affect-guide-card--amber overflow-hidden rounded-md",
  sky: "affect-tint-accent overflow-hidden rounded-md",
};

export function GuideCardGroup({ accent, refPanel, children }: GuideCardGroupProps) {
  return (
    <div className={GROUP_CLASS[accent]}>
      <div className="px-3 pt-2.5">{children}</div>
      <div className="px-3 pb-2.5 pt-1">{refPanel}</div>
    </div>
  );
}
