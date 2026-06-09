import { MousePointerClick, Sparkles } from "lucide-react";
import type { AffectTurnRecord, RelationshipSnapshot } from "../../types";
import {
  inferUserMood,
  relationshipStageLabel,
  resolveAgentMood,
  resolveAttitudeSummary,
} from "../../lib/affectPresentation";
import { VadRadarChart } from "../VadRadarChart";

interface AffectRoundSnapshotHeroProps {
  snapshot: AffectTurnRecord | null;
  focusedRoundLabel?: string | null;
  relationship?: RelationshipSnapshot | null;
}

export function AffectRoundSnapshotHero({
  snapshot,
  focusedRoundLabel,
  relationship,
}: AffectRoundSnapshotHeroProps) {
  if (!snapshot) {
    return (
      <div className="flex flex-col items-center rounded-lg border border-dashed border-border/60 bg-muted/15 px-4 py-8 text-center">
        <MousePointerClick className="mb-2.5 h-5 w-5 text-muted-foreground/70" aria-hidden />
        <p className="text-xs font-medium text-muted-foreground">先选一轮对话</p>
        <p className="mt-1.5 max-w-[14rem] text-[11px] leading-relaxed text-muted-foreground/90">
          点击左侧记录，这里会展示该轮你与助手的情绪快照与态度摘要。
        </p>
      </div>
    );
  }

  const rel = snapshot.relationship ?? relationship ?? null;
  const agentVad = snapshot.agentVadAfter ?? snapshot.agentVadTarget;
  const userLayers = [
    {
      point: snapshot.userAffectVad,
      stroke: "#8b5cf6",
      fill: "#8b5cf6",
      fillOpacity: 0.18,
      strokeWidth: 1.6,
    },
  ];
  const agentLayers = agentVad
    ? [
        {
          point: agentVad,
          stroke: "#64748b",
          fill: "#64748b",
          fillOpacity: 0.14,
          strokeWidth: 1.6,
        },
      ]
    : [];

  return (
    <div className="space-y-3">
      {focusedRoundLabel ? (
        <p className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          <Sparkles className="h-3 w-3" aria-hidden />
          {focusedRoundLabel}
        </p>
      ) : null}
      <div className="flex flex-wrap items-start justify-center gap-6 rounded-lg border border-border/30 bg-muted/12 p-4">
        <div className="text-center">
          <p className="mb-2 text-[10px] font-medium tracking-wide text-muted-foreground">你</p>
          <VadRadarChart size={92} layers={userLayers} showLabels className="text-border" />
          <p className="mt-2 text-xs text-foreground">{inferUserMood(snapshot.userAffectVad).label}</p>
        </div>
        {agentVad ? (
          <div className="text-center">
            <p className="mb-2 text-[10px] font-medium tracking-wide text-muted-foreground">助手</p>
            <VadRadarChart size={92} layers={agentLayers} showLabels className="text-border" />
            <p className="mt-2 text-xs text-foreground">
              {resolveAgentMood(snapshot)?.mood.label ?? "—"}
            </p>
          </div>
        ) : (
          <div className="flex min-h-[92px] items-center text-xs text-muted-foreground">助手状态生成中…</div>
        )}
      </div>
      <dl className="space-y-2 rounded-lg bg-muted/15 px-3 py-2.5 text-[11px]">
        <div className="flex gap-2">
          <dt className="w-10 shrink-0 text-muted-foreground">态度</dt>
          <dd className="min-w-0 text-foreground">{resolveAttitudeSummary(snapshot)}</dd>
        </div>
        {rel ? (
          <div className="flex gap-2">
            <dt className="w-10 shrink-0 text-muted-foreground">关系</dt>
            <dd className="text-foreground">{relationshipStageLabel(rel.stage)}</dd>
          </div>
        ) : null}
        {snapshot.userText ? (
          <div className="flex gap-2 border-t border-border/25 pt-2">
            <dt className="w-10 shrink-0 text-muted-foreground">原话</dt>
            <dd className="min-w-0 leading-relaxed text-muted-foreground">
              {snapshot.userText.length > 80 ? `${snapshot.userText.slice(0, 80)}…` : snapshot.userText}
            </dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
