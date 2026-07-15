import { PanelRightOpen, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
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
    <div className="chat-ios-header chat-ios-header--with-side liquid-glass">
      {onOpenStrategy ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="chat-ios-icon-btn h-9 w-9 shrink-0"
          aria-label="开发者工具"
          onClick={onOpenStrategy}
        >
          <PanelRightOpen className="h-5 w-5" strokeWidth={2} />
        </Button>
      ) : (
        <span className="w-9 shrink-0" aria-hidden="true" />
      )}
      <div className="chat-ios-header__meta">
        <h1 className="chat-ios-header__title" title={agentName}>
          {agentName}
        </h1>
        <ConnectionBanner status={connectionStatus} />
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="chat-ios-icon-btn h-9 w-9 shrink-0"
        aria-label="设置"
        onClick={onOpenSettings}
      >
        <Settings className="h-5 w-5" strokeWidth={2} />
      </Button>
    </div>
  );
}
