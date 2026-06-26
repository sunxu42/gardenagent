import { RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";

export interface SyncStatusBadgeProps {
  syncing?: boolean;
  syncFailed?: boolean;
  className?: string;
}

export function SyncStatusBadge({
  syncing = false,
  syncFailed = false,
  className,
}: SyncStatusBadgeProps): JSX.Element | null {
  if (!syncing && !syncFailed) {
    return null;
  }

  return (
    <span
      className={cn("inline-flex items-center gap-1", className)}
      role="status"
      aria-live="polite"
    >
      {syncing ? (
        <>
          <RefreshCw
            className="h-3 w-3 animate-spin motion-reduce:animate-none"
            aria-hidden
          />
          同步中…
        </>
      ) : (
        <span className="text-destructive/80">同步失败</span>
      )}
    </span>
  );
}
