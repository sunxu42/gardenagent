import { Bot } from "lucide-react";
import type { AffectTurnRecord, RelationshipSnapshot, VadPoint } from "../../types";
import { resolveAgentMood, resolveAttitudeSummary } from "../../lib/affectPresentation";
import { MoodBadge } from "./MoodBadge";
import { RelationshipMeters } from "./RelationshipMeters";
import { VadCompactBlock } from "./VadCompactBlock";

interface AffectStatusOverviewProps {
  focusedRecord?: AffectTurnRecord | null;
  focusedRoundLabel?: string | null;
  currentRelationship?: RelationshipSnapshot | null;
  currentAgentVad?: VadPoint | null;
}

export function AffectStatusOverview({
  focusedRecord,
  focusedRoundLabel,
  currentRelationship,
  currentAgentVad,
}: AffectStatusOverviewProps) {
  const rel = focusedRecord?.relationship ?? currentRelationship ?? null;
  const agentVad =
    focusedRecord?.agentVadAfter ??
    focusedRecord?.agentVadTarget ??
    currentAgentVad ??
    null;
  const agentMood = focusedRecord ? resolveAgentMood(focusedRecord) : null;
  const attitude = focusedRecord ? resolveAttitudeSummary(focusedRecord) : null;

  return (
    <div className="space-y-4">
      {focusedRoundLabel ? (
        <p className="text-[10px] font-medium text-muted-foreground">{focusedRoundLabel}</p>
      ) : null}

      <div className="space-y-2 rounded-md border border-amber-500/15 bg-amber-500/[0.06] px-3 py-2.5">
        <p className="text-xs font-medium text-foreground">关系</p>
        <RelationshipMeters relationship={rel} compact />
      </div>

      <div className="space-y-2 rounded-md border border-sky-500/15 bg-sky-500/[0.06] px-3 py-2.5">
        <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
          <Bot className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
          助手
        </p>
        {agentMood ? (
          <MoodBadge
            label={agentMood.mood.label}
            tone={agentMood.mood.tone}
            sublabel={agentMood.intensity}
          />
        ) : (
          <p className="text-[11px] text-muted-foreground">暂无数据</p>
        )}
        {agentVad ? (
          <VadCompactBlock
            title="VAD"
            accentClass="bg-sky-500/[0.05]"
            point={agentVad}
          />
        ) : null}
        {attitude ? (
          <p className="text-[11px] text-muted-foreground">
            <span className="text-foreground/85">态度 </span>
            {attitude}
          </p>
        ) : null}
      </div>
    </div>
  );
}
