import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ConnectionStatus } from "../types";
import { ConnectionBanner } from "./ConnectionBanner";

interface HeaderBarProps {
  agentName: string;
  connectionStatus: ConnectionStatus;
  onOpenSettings: () => void;
}

export function HeaderBar({ agentName, connectionStatus, onOpenSettings }: HeaderBarProps) {
  return (
    <div className="grid min-h-[52px] grid-cols-[1fr_40px] items-center gap-2 rounded-xl border bg-card px-3 py-2 shadow-sm md:min-h-[56px] md:px-4">
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
