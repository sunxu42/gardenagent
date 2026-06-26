import { Activity, Code2 } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import {
  RailListPane,
  RailPanelRoot,
  RailPanelScroll,
  RailSidebarGroup,
} from "@/components/rail/RailPanelShell";
import { RailToolbarButton } from "@/components/rail/RailToolbarButton";

import type { AffectLockState, AffectTurnRecord, EmotionProfile, RelationshipSnapshot, VadPoint } from "../types";
import { AffectGuidePanel } from "./AffectGuidePanel";
import { AffectTurnCard } from "./AffectTurnCard";

const DEV_MODE_KEY = "garden-affect-dev-mode";

export interface AffectDebugPanelProps {
  history?: AffectTurnRecord[];
  currentAgentVad?: VadPoint | null;
  baselineVad?: VadPoint | null;
  emotionProfile?: EmotionProfile | null;
  currentRelationship?: RelationshipSnapshot | null;
  affectLock: AffectLockState;
  onToggleAffectLock: (dimension: "relationship" | "agent_vad", refId: string) => void;
}

function readDevMode(): boolean {
  try {
    return localStorage.getItem(DEV_MODE_KEY) === "1";
  } catch {
    return false;
  }
}

export function AffectDebugPanel({
  history,
  currentAgentVad,
  baselineVad,
  emotionProfile,
  currentRelationship,
  affectLock,
  onToggleAffectLock,
}: AffectDebugPanelProps) {
  const [devMode, setDevMode] = useState(readDevMode);

  const safeHistory = Array.isArray(history) ? history : [];

  const toggleDevMode = useCallback(() => {
    setDevMode((prevMode) => {
      const next = !prevMode;
      try {
        localStorage.setItem(DEV_MODE_KEY, next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const focusedRecord = safeHistory[0] ?? null;
  const prevFocusedRecord = safeHistory[1] ?? null;

  const focusedRoundLabel = useMemo(() => {
    if (!focusedRecord) {
      return null;
    }
    const idx = safeHistory.findIndex((h) => h.turnId === focusedRecord.turnId);
    if (idx < 0) {
      return null;
    }
    return `第 ${safeHistory.length - idx} 轮`;
  }, [focusedRecord, safeHistory]);

  return (
    <RailPanelRoot>
      <RailSidebarGroup>
        <RailListPane>
          <RailPanelHeader
            level={3}
            icon={Activity}
            title="情绪记录"
            actions={
              <RailToolbarButton
                pressed={devMode}
                icon={<Code2 className="h-3.5 w-3.5" />}
                title="显示原始数据"
                onClick={toggleDevMode}
              >
                开发者
              </RailToolbarButton>
            }
          />

          <RailPanelScroll className="px-4 pb-6 pt-2">
            {safeHistory.length === 0 ? (
              <p className="pt-12 text-center text-xs text-muted-foreground">发送消息后显示记录</p>
            ) : (
              <ul className="affect-turn-list space-y-2" aria-label="情绪记录">
                {safeHistory.map((item, index) => (
                  <AffectTurnCard
                    key={item.turnId}
                    record={item}
                    prevRecord={safeHistory[index + 1] ?? null}
                    index={index}
                    total={safeHistory.length}
                    devMode={devMode}
                  />
                ))}
              </ul>
            )}
          </RailPanelScroll>
        </RailListPane>

        <AffectGuidePanel
          focusedRecord={focusedRecord}
          prevFocusedRecord={prevFocusedRecord}
          focusedRoundLabel={focusedRoundLabel}
          currentRelationship={currentRelationship}
          currentAgentVad={currentAgentVad}
          emotionProfile={emotionProfile}
          agentBaselineVad={baselineVad}
          affectLock={affectLock}
          onToggleAffectLock={onToggleAffectLock}
        />
      </RailSidebarGroup>
    </RailPanelRoot>
  );
}
