import { EvalRunProgressView } from "@/features/test/EvalRunProgressView";
import { eventsToTimeline } from "@/features/test/evalHistoryTimeline";
import type { EvalRunPhase } from "@/features/test/evalProgress";
import type { EvalRunResponse, PersistedEventDTO } from "@/features/test/types";

function statusToPhase(status: EvalRunResponse["status"] | undefined): EvalRunPhase {
  if (status === "failed") {
    return "failed";
  }
  if (status === "cancelled") {
    return "cancelled";
  }
  if (status === "running") {
    return "agent";
  }
  return "completed";
}

interface EvalRunHistoryTimelineProps {
  events?: PersistedEventDTO[];
  status?: EvalRunResponse["status"];
  tier?: EvalRunResponse["tier"];
  scenarioId?: string | null;
}

export function EvalRunHistoryTimeline({
  events = [],
  status,
  tier,
  scenarioId,
}: EvalRunHistoryTimelineProps): JSX.Element | null {
  const timeline = eventsToTimeline(events);
  if (timeline.length === 0) {
    return null;
  }

  return (
    <EvalRunProgressView
      readOnly
      state={{
        status: status === "running" ? "running" : status === "failed" ? "failed" : status === "cancelled" ? "cancelled" : "completed",
        progressMessage: "历史过程记录",
        phase: statusToPhase(status),
        agentProgress: null,
        judgeProgress: null,
        timeline,
        scenarioId: scenarioId ?? null,
        tier: tier ?? null,
      }}
    />
  );
}
