import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import "./rail-panel-header.css";

export interface RailPanelHeaderProps {
  icon: LucideIcon;
  title: string;
  /** inline meta to the right of the title (same row) */
  titleTrailing?: ReactNode;
  subtitle?: string;
  actions?: ReactNode;
  /** h2 for panel root, h3 for inner sections */
  level?: 2 | 3;
  className?: string;
  /** invisible action placeholder for column alignment */
  actionPlaceholder?: boolean;
}

export function RailPanelHeader({
  icon: Icon,
  title,
  titleTrailing,
  subtitle,
  actions,
  level = 2,
  className,
  actionPlaceholder,
}: RailPanelHeaderProps): JSX.Element {
  const TitleTag = level === 2 ? "h2" : "h3";
  const titleNode = (
    <TitleTag className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
      <span className="rail-panel-header__icon">
        <Icon className="h-3.5 w-3.5" aria-hidden />
      </span>
      <span className="truncate">{title}</span>
      {titleTrailing ? (
        <span className="shrink-0 text-xs font-normal text-muted-foreground">{titleTrailing}</span>
      ) : null}
    </TitleTag>
  );

  return (
    <header className={cn("rail-panel-header shrink-0", className)}>
      <div className="rail-panel-header__row">
        {subtitle ? (
          <div className="min-w-0 flex-1">
            {titleNode}
            <p className="mt-0.5 truncate pl-[calc(1.5rem+0.5rem)] text-[11px] leading-snug text-muted-foreground">
              {subtitle}
            </p>
          </div>
        ) : (
          titleNode
        )}
        {actions ? <div className="rail-panel-header__actions">{actions}</div> : null}
        {!actions && actionPlaceholder ? (
          <span className="invisible shrink-0 px-2.5 py-1.5 text-[11px]" aria-hidden>
            开发者
          </span>
        ) : null}
      </div>
    </header>
  );
}
