import { useEffect, useRef, useState } from "react";

import { RailDetailPane, RailListPane, RailSidebarGroup } from "@/components/rail/RailPanelShell";
import { EvalDomainBreadcrumb } from "@/features/test/EvalDomainBreadcrumb";
import { EvalDomainModeTabs } from "@/features/test/EvalDomainModeTabs";
import { EvalDomainRunDock } from "@/features/test/EvalDomainRunDock";
import { EvalDomainScenarioPane } from "@/features/test/EvalDomainScenarioPane";
import { EvalExploratoryPane } from "@/features/test/EvalExploratoryPane";
import { useEvalRun } from "@/features/test/EvalRunProvider";
import {
  getFocusedItem,
  getNextPendingItem,
  getRunningItem,
} from "@/features/test/evalBatchTypes";
import { getErrorMessage } from "@/features/test/evalFormConstants";
import type { DomainMode, EmotionEvalRequest } from "@/features/test/types";
import { getOrCreateUserId } from "@/lib/userId";
import { startExploratoryEvalAsync } from "@/services/eval/evalApi";
import { cancelEvalRun, startScenarioEvalAsync } from "@/services/eval/scenarioApi";

interface EvalDomainWorkspaceProps {
  domainId: string;
  domainLabel: string;
  coverageScore: number;
  passScore: number;
  onBack: () => void;
}

export function EvalDomainWorkspace({
  domainId,
  domainLabel,
  coverageScore,
  passScore,
  onBack,
}: EvalDomainWorkspaceProps): JSX.Element {
  const { state: evalRunState, dispatch: dispatchEvalRun } = useEvalRun();
  const [mode, setMode] = useState<DomainMode>("smoke");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const advanceInFlightRef = useRef(false);

  const showExploratory = domainId === "emotion";
  const scenarioRunning = evalRunState.batchStatus === "running";
  const focusedItem = getFocusedItem(evalRunState);
  const focusedLive = focusedItem?.live;
  const exploratoryRunning = scenarioRunning && focusedLive?.tier === "exploratory";
  const scenarioBatchRunning = scenarioRunning && focusedLive?.tier !== "exploratory";

  const handleModeChange = (nextMode: DomainMode): void => {
    setMode(nextMode);
    setSelectedIds([]);
    setError(null);
  };

  const startScenarioEval = async (scenarioId: string): Promise<void> => {
    setError(null);
    const started = await startScenarioEvalAsync(scenarioId, getOrCreateUserId());
    dispatchEvalRun({
      type: "RUN_STARTED",
      payload: {
        runId: started.run_id,
        scenarioId: started.scenario_id,
        tier: started.tier,
      },
    });
  };

  const handleScenarioRun = async (): Promise<void> => {
    if (scenarioBatchRunning || exploratoryRunning || selectedIds.length === 0) {
      return;
    }

    dispatchEvalRun({
      type: "BATCH_STARTED",
      payload: { scenarioIds: selectedIds },
    });

    try {
      await startScenarioEval(selectedIds[0]);
    } catch (runError) {
      dispatchEvalRun({ type: "RESET" });
      setError(getErrorMessage(runError));
    }
  };

  const handleScenarioCancel = async (): Promise<void> => {
    dispatchEvalRun({ type: "BATCH_CANCEL" });
    const runningItem = getRunningItem(evalRunState);
    if (!runningItem?.live.activeRunId) {
      return;
    }
    try {
      await cancelEvalRun(runningItem.live.activeRunId);
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  const handleExploratoryRun = async (request: EmotionEvalRequest): Promise<void> => {
    if (exploratoryRunning || scenarioBatchRunning) {
      return;
    }

    setError(null);
    dispatchEvalRun({
      type: "BATCH_STARTED",
      payload: { scenarioIds: ["exploratory"] },
    });

    try {
      const started = await startExploratoryEvalAsync(request, getOrCreateUserId());
      dispatchEvalRun({
        type: "RUN_STARTED",
        payload: {
          runId: started.run_id,
          scenarioId: started.scenario_id,
          tier: started.tier,
        },
      });
    } catch (runError) {
      dispatchEvalRun({ type: "RESET" });
      setError(getErrorMessage(runError));
    }
  };

  const handleExploratoryCancel = async (): Promise<void> => {
    dispatchEvalRun({ type: "BATCH_CANCEL" });
    const runningItem = getRunningItem(evalRunState);
    if (!runningItem?.live.activeRunId) {
      return;
    }
    try {
      await cancelEvalRun(runningItem.live.activeRunId);
    } catch (runError) {
      setError(getErrorMessage(runError));
    }
  };

  useEffect(() => {
    if (mode === "exploratory") {
      return;
    }
    if (evalRunState.batchStatus !== "running") {
      advanceInFlightRef.current = false;
      return;
    }
    if (getRunningItem(evalRunState)) {
      return;
    }
    const nextItem = getNextPendingItem(evalRunState);
    if (!nextItem || advanceInFlightRef.current) {
      return;
    }
    advanceInFlightRef.current = true;
    dispatchEvalRun({ type: "BATCH_ADVANCE" });
    startScenarioEval(nextItem.scenarioId)
      .catch((runError: unknown) => {
        dispatchEvalRun({ type: "RESET" });
        setError(getErrorMessage(runError));
      })
      .finally(() => {
        advanceInFlightRef.current = false;
      });
  }, [evalRunState.batchStatus, evalRunState.items, mode]);

  const dockError = error ?? focusedLive?.error ?? null;
  const meta = `覆盖 ${Math.round(coverageScore * 100)}% · 通过 ${Math.round(passScore * 100)}%`;

  return (
    <div className="eval-domain-workspace">
      <EvalDomainBreadcrumb domainLabel={domainLabel} meta={meta} onBack={onBack} />

      <div className="eval-domain-workspace__toolbar">
        <EvalDomainModeTabs mode={mode} showExploratory={showExploratory} onChange={handleModeChange} />
      </div>

      <RailSidebarGroup className="eval-domain-workspace__body">
        <RailListPane className="eval-domain-workspace__list">
          {mode === "exploratory" ? (
            <EvalExploratoryPane
              running={exploratoryRunning}
              onCancel={() => void handleExploratoryCancel()}
              onRun={(request) => void handleExploratoryRun(request)}
            />
          ) : (
            <EvalDomainScenarioPane
              disabled={scenarioBatchRunning}
              domainId={domainId}
              running={scenarioBatchRunning}
              selectedIds={selectedIds}
              tier={mode}
              onCancel={() => void handleScenarioCancel()}
              onChange={setSelectedIds}
              onRun={() => void handleScenarioRun()}
            />
          )}
        </RailListPane>

        <RailDetailPane className="eval-domain-workspace__detail">
          <EvalDomainRunDock
            error={dockError}
            mode={mode === "exploratory" ? "exploratory" : "scenario"}
          />
        </RailDetailPane>
      </RailSidebarGroup>
    </div>
  );
}
