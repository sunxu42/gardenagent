import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import "./panel-state.css";

interface PanelEmptyProps {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  fill?: boolean;
}

export function PanelEmpty({
  title,
  description,
  action,
  className,
  fill = true,
}: PanelEmptyProps): JSX.Element {
  return (
    <div className={cn("panel-state", fill && "panel-state--fill", className)}>
      <div className="panel-state__card">
        <p className="panel-state__title">{title}</p>
        {description ? <p className="panel-state__desc">{description}</p> : null}
        {action}
      </div>
    </div>
  );
}
