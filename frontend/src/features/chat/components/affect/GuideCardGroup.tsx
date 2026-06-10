import type { ReactNode } from "react";

interface GuideCardGroupProps {
  accent: "amber" | "sky";
  refPanel: ReactNode;
  children: ReactNode;
}

const GROUP_ACCENT: Record<GuideCardGroupProps["accent"], { shell: string; bg: string }> = {
  amber: {
    shell: "border-amber-500/15",
    bg: "bg-amber-500/[0.06]",
  },
  sky: {
    shell: "border-sky-500/15",
    bg: "bg-sky-500/[0.06]",
  },
};

export function GuideCardGroup({ accent, refPanel, children }: GuideCardGroupProps) {
  const tint = GROUP_ACCENT[accent];

  return (
    <div className={`overflow-hidden rounded-md border ${tint.shell} ${tint.bg}`}>
      <div className="px-3 pt-2.5">{children}</div>
      <div className="px-3 pb-2.5 pt-1">{refPanel}</div>
    </div>
  );
}
