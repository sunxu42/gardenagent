import { Code2, ListOrdered } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
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
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);

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

  const focusedRecord = useMemo(() => {
    if (selectedTurnId) {
      return safeHistory.find((h) => h.turnId === selectedTurnId) ?? safeHistory[0] ?? null;
    }
    return safeHistory[0] ?? null;
  }, [safeHistory, selectedTurnId]);

  const focusedRoundLabel = useMemo(() => {
    if (!focusedRecord) return null;
    const idx = safeHistory.findIndex((h) => h.turnId === focusedRecord.turnId);
    if (idx < 0) return null;
    return `第 ${safeHistory.length - idx} 轮`;
  }, [focusedRecord, safeHistory]);

  return (
    <div className="affect-panel-root h-full min-h-0 max-h-full w-full overflow-hidden flex">
      <div className="affect-sidebar-group h-full min-h-0 max-h-full overflow-hidden">
        <aside className="affect-history-panel flex min-h-0 flex-1 flex-col overflow-hidden">
          <header className="affect-rail-header shrink-0">
            <div className="affect-rail-header__row">
              <h3 className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
                <span className="affect-rail-header__icon">
                  <ListOrdered className="h-3.5 w-3.5" aria-hidden />
                </span>
                情绪记录
              </h3>
              <button
                type="button"
                onClick={toggleDevMode}
                className={`shrink-0 cursor-pointer rounded-md px-2.5 py-1.5 text-[11px] font-medium transition-colors duration-200 ${
                  devMode
                    ? "bg-muted/50 text-foreground"
                    : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                }`}
                aria-pressed={devMode}
                title="显示原始 JSON"
              >
                <span className="inline-flex items-center gap-1.5">
                  <Code2 className="h-3.5 w-3.5" aria-hidden />
                  开发者
                </span>
              </button>
            </div>
          </header>

          <div className="affect-panel-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-6 pt-2">
            {safeHistory.length === 0 ? (
              <p className="pt-12 text-center text-xs text-muted-foreground">发送消息后显示记录</p>
            ) : (
              <ul className="space-y-2">
                {safeHistory.map((item, index) => (
                  <AffectTurnCard
                    key={item.turnId}
                    record={item}
                    prevRecord={safeHistory[index + 1] ?? null}
                    index={index}
                    total={safeHistory.length}
                    devMode={devMode}
                    selected={selectedTurnId === item.turnId}
                    onSelect={() => setSelectedTurnId(item.turnId)}
                  />
                ))}
              </ul>
            )}
          </div>
        </aside>

        <AffectGuidePanel
          focusedRecord={focusedRecord}
          focusedRoundLabel={focusedRoundLabel}
          currentRelationship={currentRelationship}
          currentAgentVad={currentAgentVad}
          emotionProfile={emotionProfile}
          agentBaselineVad={baselineVad}
          affectLock={affectLock}
          onToggleAffectLock={onToggleAffectLock}
        />
      </div>
    </div>
  );
}
