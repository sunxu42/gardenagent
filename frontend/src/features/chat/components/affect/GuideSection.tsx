import type { ReactNode } from "react";

interface GuideAnchorSectionProps {
  id: string;
  title: string;
  children: ReactNode;
  accent?: "amber" | "sky" | "indigo" | "violet";
}

const SECTION_CLASS: Record<NonNullable<GuideAnchorSectionProps["accent"]>, string> = {
  amber: "affect-guide-section affect-guide-section--amber",
  sky: "affect-guide-section affect-guide-section--sky",
  indigo: "affect-guide-section affect-guide-section--indigo",
  violet: "affect-guide-section affect-guide-section--violet",
};

export function GuideAnchorSection({
  id,
  title,
  children,
  accent = "sky",
}: GuideAnchorSectionProps) {
  return (
    <section id={id} className={`scroll-mt-[3.75rem] py-3 pl-3.5 pr-3 ${SECTION_CLASS[accent]}`}>
      <h4 className="mb-2.5 text-[13px] font-medium text-foreground">{title}</h4>
      {children}
    </section>
  );
}

interface GuideModuleCardProps {
  label: string;
  detail: string;
  /** 补充说明（如衰减公式），显示在 detail 下方 */
  note?: string;
  accent: "violet" | "sky" | "amber" | "slate";
  icon?: ReactNode;
}

const MODULE_CLASS: Record<GuideModuleCardProps["accent"], string> = {
  violet: "affect-guide-card affect-guide-card--violet",
  sky: "affect-tint-accent",
  amber: "affect-guide-card affect-guide-card--amber",
  slate: "affect-guide-inset affect-guide-inset--sky",
};

const MODULE_DOT: Record<GuideModuleCardProps["accent"], string> = {
  violet: "bg-violet-500",
  sky: "affect-dot-accent",
  amber: "bg-amber-500",
  slate: "bg-sky-500",
};

export function GuideModuleCard({ label, detail, note, accent, icon }: GuideModuleCardProps) {
  return (
    <div className={`rounded-md px-3 py-2.5 ${MODULE_CLASS[accent]}`}>
      <p className="flex items-center gap-2 text-xs font-medium text-foreground">
        {icon ? (
          <span className="text-muted-foreground">{icon}</span>
        ) : (
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${MODULE_DOT[accent]}`} aria-hidden />
        )}
        {label}
      </p>
      <p className="mt-1 pl-3.5 text-[11px] leading-relaxed text-muted-foreground">{detail}</p>
      {note ? (
        <p className="mt-1.5 pl-3.5 text-[10px] leading-relaxed text-muted-foreground/90 whitespace-pre-line">
          {note}
        </p>
      ) : null}
    </div>
  );
}
