import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import "./panel-state.css";

interface PanelLoadingProps {
  label?: ReactNode;
  className?: string;
  fill?: boolean;
}

export function PanelLoading({
  label = "加载中…",
  className,
  fill = true,
}: PanelLoadingProps): JSX.Element {
  return (
    <div
      className={cn("panel-state", fill && "panel-state--fill", className)}
      role="status"
      aria-live="polite"
    >
      <div className="panel-state__card">
        <Loader2
          className="panel-state__spinner h-4 w-4 animate-spin motion-reduce:animate-none"
          aria-hidden
        />
        <span className="panel-state__label">{label}</span>
      </div>
    </div>
  );
}
