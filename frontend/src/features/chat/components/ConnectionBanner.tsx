import { Badge } from "@/components/ui/badge";
import type { ConnectionStatus } from "../types";
import { cn } from "@/lib/utils";

interface ConnectionBannerProps {
  status: ConnectionStatus;
}

export function ConnectionBanner({ status }: ConnectionBannerProps) {
  const isOnline = status === "online";

  return (
    <Badge
      role="status"
      variant="outline"
      aria-label={isOnline ? "在线" : "离线"}
      className={cn(
        "chat-ios-status rounded-full border-0 bg-transparent px-0 py-0 font-normal shadow-none",
        isOnline ? "chat-ios-status--online" : "chat-ios-status--offline",
      )}
    >
      <span className="chat-ios-status__dot" aria-hidden="true" />
      {isOnline ? "在线" : "离线"}
    </Badge>
  );
}
