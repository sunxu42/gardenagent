import type { ReactNode } from "react";

interface GuideAnchorSectionProps {
  id: string;
  title: string;
  children: ReactNode;
  accent?: "amber" | "slate" | "indigo" | "violet";
}

const ACCENT_BAR: Record<NonNullable<GuideAnchorSectionProps["accent"]>, string> = {
  amber: "border-l-amber-500/50",
  slate: "border-l-slate-400/45",
  indigo: "border-l-indigo-500/45",
  violet: "border-l-violet-500/45",
};

const ACCENT_BG: Record<NonNullable<GuideAnchorSectionProps["accent"]>, string> = {
  amber: "bg-amber-500/[0.04]",
  slate: "bg-muted/15",
  indigo: "bg-indigo-500/[0.04]",
  violet: "bg-violet-500/[0.04]",
};

export function GuideAnchorSection({
  id,
  title,
  children,
  accent = "slate",
}: GuideAnchorSectionProps) {
  return (
    <section
      id={id}
      className={`scroll-mt-[3.75rem] rounded-lg border border-border/30 border-l-[3px] py-3 pl-3.5 pr-3 ${ACCENT_BAR[accent]} ${ACCENT_BG[accent]}`}
    >
      <h4 className="mb-2.5 text-[13px] font-medium text-foreground">{title}</h4>
      {children}
    </section>
  );
}

interface GuideModuleCardProps {
  label: string;
  detail: string;
  accent: "violet" | "sky" | "amber" | "slate";
  icon?: ReactNode;
}

const MODULE_TINT: Record<GuideModuleCardProps["accent"], string> = {
  violet: "border border-violet-500/15 bg-violet-500/[0.05]",
  sky: "border border-sky-500/15 bg-sky-500/[0.05]",
  amber: "border border-amber-500/15 bg-amber-500/[0.05]",
  slate: "border border-border/25 bg-muted/20",
};

const MODULE_DOT: Record<GuideModuleCardProps["accent"], string> = {
  violet: "bg-violet-500",
  sky: "bg-sky-500",
  amber: "bg-amber-500",
  slate: "bg-muted-foreground/50",
};

export function GuideModuleCard({ label, detail, accent, icon }: GuideModuleCardProps) {
  return (
    <div className={`rounded-md px-3 py-2.5 ${MODULE_TINT[accent]}`}>
      <p className="flex items-center gap-2 text-xs font-medium text-foreground">
        {icon ? (
          <span className="text-muted-foreground">{icon}</span>
        ) : (
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${MODULE_DOT[accent]}`} aria-hidden />
        )}
        {label}
      </p>
      <p className="mt-1 pl-3.5 text-[11px] leading-relaxed text-muted-foreground">{detail}</p>
    </div>
  );
}
