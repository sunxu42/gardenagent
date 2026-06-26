import { PanelRightOpen, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "../types";
import { ConnectionBanner } from "./ConnectionBanner";

interface HeaderBarProps {
  agentName: string;
  connectionStatus: ConnectionStatus;
  onOpenSettings: () => void;
  onOpenStrategy?: () => void;
}

export function HeaderBar({
  agentName,
  connectionStatus,
  onOpenSettings,
  onOpenStrategy,
}: HeaderBarProps) {
  return (
    <div
      className={cn(
        "grid min-h-[52px] items-center gap-2 rounded-xl border bg-card px-3 py-2 shadow-sm md:min-h-[56px] md:px-4",
        onOpenStrategy ? "grid-cols-[auto_1fr_auto]" : "grid-cols-[1fr_auto]",
      )}
    >
      {onOpenStrategy ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="cursor-pointer text-muted-foreground hover:bg-primary/12 hover:text-primary active:bg-primary/20 active:text-primary"
          aria-label="开发者工具"
          onClick={onOpenStrategy}
        >
          <PanelRightOpen className="h-5 w-5" />
        </Button>
      ) : null}
      <div className="flex min-w-0 items-center justify-center gap-2">
        <h1 className="m-0 min-w-0 truncate text-lg text-card-foreground" title={agentName}>
          {agentName}
        </h1>
        <ConnectionBanner status={connectionStatus} />
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="cursor-pointer text-muted-foreground hover:bg-primary/12 hover:text-primary active:bg-primary/20 active:text-primary"
        aria-label="设置"
        onClick={onOpenSettings}
      >
        <Settings className="h-5 w-5" />
      </Button>
    </div>
  );
}
