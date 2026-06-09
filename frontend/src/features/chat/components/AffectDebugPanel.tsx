import { Code2, ListOrdered } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import type { AffectTurnRecord, EmotionProfile, RelationshipSnapshot, VadPoint } from "../types";
import { AffectGuidePanel, AffectGuideToggle } from "./AffectGuidePanel";
import { AffectTurnCard } from "./AffectTurnCard";

const DEV_MODE_KEY = "garden-affect-dev-mode";
const GUIDE_OPEN_KEY = "garden-affect-guide-open";

export interface AffectDebugPanelProps {
  history?: AffectTurnRecord[];
  currentAgentVad?: VadPoint | null;
  baselineVad?: VadPoint | null;
  emotionProfile?: EmotionProfile | null;
  currentRelationship?: RelationshipSnapshot | null;
}

function readDevMode(): boolean {
  try {
    return localStorage.getItem(DEV_MODE_KEY) === "1";
  } catch {
    return false;
  }
}

function readGuideOpen(): boolean {
  try {
    return localStorage.getItem(GUIDE_OPEN_KEY) === "1";
  } catch {
    return false;
  }
}

export function AffectDebugPanel({
  history,
  baselineVad,
  emotionProfile,
  currentRelationship,
}: AffectDebugPanelProps) {
  const [devMode, setDevMode] = useState(readDevMode);
  const [guideOpen, setGuideOpen] = useState(readGuideOpen);
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

  const persistGuideOpen = useCallback((next: boolean) => {
    try {
      localStorage.setItem(GUIDE_OPEN_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, []);

  const toggleGuide = useCallback(() => {
    setGuideOpen((prev) => {
      const next = !prev;
      persistGuideOpen(next);
      return next;
    });
  }, [persistGuideOpen]);

  const closeGuide = useCallback(() => {
    setGuideOpen(false);
    persistGuideOpen(false);
  }, [persistGuideOpen]);

  const openGuideForTurn = useCallback(
    (turnId: string) => {
      setSelectedTurnId(turnId);
      setGuideOpen(true);
      persistGuideOpen(true);
    },
    [persistGuideOpen],
  );

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
    <div
      className={`affect-panel-root h-full min-h-0 max-h-full w-full overflow-hidden flex ${guideOpen ? "affect-panel-root--guide-open" : ""}`}
    >
      <div
        className={`affect-sidebar-group h-full min-h-0 max-h-full overflow-hidden ${guideOpen ? "affect-sidebar-group--guide-open" : ""}`}
      >
        <aside className="affect-history-panel flex min-h-0 flex-1 flex-col overflow-hidden">
          <header className="affect-rail-header shrink-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-muted/50 text-muted-foreground">
                    <ListOrdered className="h-3.5 w-3.5" aria-hidden />
                  </span>
                  情绪记录
                </h3>
                <p className="mt-1.5 pl-8 text-[11px] leading-relaxed text-muted-foreground/90">
                  每轮 V·A·D 与态度；点击条目可展开模块说明
                </p>
              </div>
              <div className="flex shrink-0 flex-col gap-1.5">
                <AffectGuideToggle open={guideOpen} onClick={toggleGuide} />
                <button
                  type="button"
                  onClick={toggleDevMode}
                  className={`cursor-pointer rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors duration-200 ${
                    devMode
                      ? "border-border bg-muted/50 text-foreground"
                      : "border-transparent bg-transparent text-muted-foreground hover:bg-muted/40 hover:text-foreground"
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
            </div>

          </header>

          <div className="affect-panel-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-6 pt-2">
            {safeHistory.length === 0 ? (
              <p className="pt-12 text-center text-xs leading-relaxed text-muted-foreground">
                发送消息后，每轮数值会列在这里。
              </p>
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
                    selected={guideOpen && selectedTurnId === item.turnId}
                    onSelect={() => openGuideForTurn(item.turnId)}
                  />
                ))}
              </ul>
            )}
          </div>
        </aside>

        <AffectGuidePanel
          open={guideOpen}
          onClose={closeGuide}
          focusedRecord={focusedRecord}
          focusedRoundLabel={focusedRoundLabel}
          currentRelationship={currentRelationship}
          emotionProfile={emotionProfile}
          agentBaselineVad={baselineVad}
        />
      </div>
    </div>
  );
}
