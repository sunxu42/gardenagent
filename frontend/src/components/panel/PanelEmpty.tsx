import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import "./panel-state.css";

type PanelEmptyVariant = "card" | "hero" | "compact" | "inline";

interface PanelEmptyProps {
  title: string;
  description?: string;
  action?: ReactNode;
  actions?: ReactNode;
  icon?: LucideIcon;
  variant?: PanelEmptyVariant;
  className?: string;
  fill?: boolean;
}

const ICON_SIZE: Record<Exclude<PanelEmptyVariant, "card" | "inline">, string> = {
  hero: "h-8 w-8",
  compact: "h-4 w-4",
};

export function PanelEmpty({
  title,
  description,
  action,
  actions,
  icon: Icon,
  variant = "card",
  className,
  fill = true,
}: PanelEmptyProps): JSX.Element {
  const resolvedActions = actions ?? action;

  if (variant === "inline") {
    return (
      <p className={cn("panel-state panel-state--inline", fill && "panel-state--fill", className)}>
        {title}
      </p>
    );
  }

  const isCard = variant === "card";
  const iconSize = variant === "hero" || variant === "compact" ? ICON_SIZE[variant] : undefined;

  return (
    <div
      className={cn(
        "panel-state",
        fill && "panel-state--fill",
        !isCard && `panel-state--${variant}`,
        className,
      )}
    >
      {isCard ? (
        <div className="panel-state__card">
          <p className="panel-state__title">{title}</p>
          {description ? <p className="panel-state__desc">{description}</p> : null}
          {resolvedActions}
        </div>
      ) : (
        <>
          {Icon && iconSize ? (
            <div className="panel-state__icon" aria-hidden>
              <Icon className={iconSize} strokeWidth={variant === "hero" ? 1.5 : 2} />
            </div>
          ) : null}
          <p className="panel-state__title">{title}</p>
          {description ? <p className="panel-state__desc">{description}</p> : null}
          {resolvedActions ? <div className="panel-state__actions">{resolvedActions}</div> : null}
        </>
      )}
    </div>
  );
}
