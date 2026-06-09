import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

interface GuideSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export function GuideSection({ title, description, children, className = "" }: GuideSectionProps) {
  return (
    <section className={className}>
      <div className="mb-3 border-l-2 border-border pl-3">
        <h4 className="text-sm font-medium leading-snug text-muted-foreground">{title}</h4>
        {description ? (
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

interface GuidePrioritySectionProps {
  priority: number;
  title: string;
  description?: string;
  children: ReactNode;
  variant?: "hero" | "default";
}

export function GuidePrioritySection({
  priority,
  title,
  description,
  children,
  variant = "default",
}: GuidePrioritySectionProps) {
  const isHero = variant === "hero";
  return (
    <section
      className={
        isHero
          ? "rounded-xl border border-border/50 bg-card/40 p-4 shadow-sm"
          : "rounded-lg border border-border/35 bg-muted/8 p-3.5"
      }
    >
      <div className={`mb-3 flex gap-2.5 ${isHero ? "items-start" : "items-center"}`}>
        <span
          className={`flex shrink-0 items-center justify-center rounded-full font-semibold tabular-nums ${
            isHero
              ? "h-6 w-6 bg-primary/10 text-[11px] text-primary"
              : "h-5 w-5 bg-muted text-[10px] text-muted-foreground"
          }`}
          aria-hidden
        >
          {priority}
        </span>
        <div className="min-w-0">
          <h4
            className={`font-medium leading-snug text-foreground ${isHero ? "text-sm" : "text-[13px]"}`}
          >
            {title}
          </h4>
          {description ? (
            <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{description}</p>
          ) : null}
        </div>
      </div>
      {children}
    </section>
  );
}

interface GuideCollapsibleSectionProps {
  priority: number;
  title: string;
  description?: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function GuideCollapsibleSection({
  priority,
  title,
  description,
  children,
  defaultOpen = false,
}: GuideCollapsibleSectionProps) {
  return (
    <details
      className="group rounded-lg border border-border/35 bg-muted/6 open:bg-muted/10"
      open={defaultOpen}
    >
      <summary className="flex cursor-pointer list-none items-start gap-2.5 px-3.5 py-3 transition-colors duration-200 hover:bg-muted/20 [&::-webkit-details-marker]:hidden">
        <span
          className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-semibold tabular-nums text-muted-foreground"
          aria-hidden
        >
          {priority}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-medium leading-snug text-foreground">{title}</p>
          {description ? (
            <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{description}</p>
          ) : null}
        </div>
        <ChevronDown
          className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 group-open:rotate-180"
          aria-hidden
        />
      </summary>
      <div className="border-t border-border/25 px-3.5 pb-3.5 pt-2">{children}</div>
    </details>
  );
}

interface GuideModuleCardProps {
  label: string;
  detail: string;
  accent: "violet" | "sky" | "amber" | "slate";
  icon?: ReactNode;
}

const ACCENT: Record<GuideModuleCardProps["accent"], string> = {
  violet: "border-l-violet-400/70 bg-muted/25",
  sky: "border-l-sky-400/70 bg-muted/20",
  amber: "border-l-amber-400/70 bg-muted/25",
  slate: "border-l-slate-400/60 bg-muted/20",
};

export function GuideModuleCard({ label, detail, accent, icon }: GuideModuleCardProps) {
  return (
    <div className={`rounded-lg border border-border/50 border-l-[3px] px-3 py-2.5 ${ACCENT[accent]}`}>
      <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
        {icon ? <span className="text-muted-foreground">{icon}</span> : null}
        {label}
      </p>
      <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{detail}</p>
    </div>
  );
}
