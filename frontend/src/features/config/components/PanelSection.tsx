import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PanelSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  fill?: boolean;
}

export function PanelSection({
  title,
  description,
  children,
  className = "",
  bodyClassName = "",
  fill = false,
}: PanelSectionProps) {
  return (
    <section className={cn("flex min-h-0 min-w-0 flex-col", fill && "h-full", className)}>
      <header className="config-desktop-panel__head shrink-0">
        <h2 className="config-desktop-panel__title">{title}</h2>
        {description ? <p className="config-desktop-panel__desc">{description}</p> : null}
      </header>
      <div className={cn("config-desktop-panel__body", fill && "flex min-h-0 flex-1 flex-col", bodyClassName)}>
        {children}
      </div>
    </section>
  );
}
