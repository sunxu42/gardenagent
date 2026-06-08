import type { ConnectionStatus } from "../types";
import { cn } from "@/lib/utils";

interface ConnectionBannerProps {
  status: ConnectionStatus;
}

export function ConnectionBanner({ status }: ConnectionBannerProps) {
  const isOnline = status === "online";

  return (
    <span
      role="status"
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-full text-xs font-medium",
        isOnline ? "text-emerald-600" : "text-destructive",
      )}
      aria-label={isOnline ? "在线" : "离线"}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", isOnline ? "bg-emerald-500" : "bg-destructive")}
        aria-hidden="true"
      />
      {isOnline ? "在线" : "离线"}
    </span>
  );
}
