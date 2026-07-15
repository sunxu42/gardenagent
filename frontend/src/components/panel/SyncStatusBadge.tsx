import { RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
    <Badge
      variant="outline"
      role="status"
      aria-live="polite"
      className={cn(
        "gap-1 rounded-md border-0 bg-transparent px-0 py-0 text-xs font-normal shadow-none",
        className,
      )}
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
    </Badge>
  );
}
