import { Bot } from "lucide-react";
import type { AffectLockState, AffectTurnRecord, RelationshipSnapshot, VadPoint } from "../../types";
import { resolveAgentMood, resolveAttitudeSummary } from "../../lib/affectPresentation";
import {
  resolveDisplayAgentVad,
  resolveLiveAgentEmotionId,
} from "../../lib/emotionReference";
import { EmotionPrototypeRefPanel } from "./EmotionPrototypeRefPanel";
import { GuideCardGroup } from "./GuideCardGroup";
import { RelationshipMeters } from "./RelationshipMeters";
import { RelationshipStageRefPanel } from "./RelationshipStageRefPanel";
import { VadCompactBlock } from "./VadCompactBlock";

interface AffectStatusOverviewProps {
  focusedRecord?: AffectTurnRecord | null;
  focusedRoundLabel?: string | null;
  currentRelationship?: RelationshipSnapshot | null;
  currentAgentVad?: VadPoint | null;
  agentBaselineVad?: VadPoint | null;
  affectLock: AffectLockState;
  onToggleAffectLock: (dimension: "relationship" | "agent_vad", refId: string) => void;
}

export function AffectStatusOverview({
  focusedRecord,
  focusedRoundLabel,
  currentRelationship,
  currentAgentVad,
  agentBaselineVad,
  affectLock,
  onToggleAffectLock,
}: AffectStatusOverviewProps) {
  const rel = focusedRecord?.relationship ?? currentRelationship ?? null;
  const liveAgentVad =
    focusedRecord?.agentVadAfter ??
    focusedRecord?.agentVadTarget ??
    currentAgentVad ??
    agentBaselineVad ??
    null;
  const agentMood = focusedRecord ? resolveAgentMood(focusedRecord) : null;
  const attitude = focusedRecord ? resolveAttitudeSummary(focusedRecord) : null;

  const liveEmotionId = resolveLiveAgentEmotionId(
    focusedRecord?.agentEmotion ?? null,
    liveAgentVad,
  );

  const displayStageId = affectLock.relationship.locked
    ? affectLock.relationship.refId
    : rel?.stage;
  const displayEmotionId = affectLock.agentVad.locked
    ? affectLock.agentVad.refId ?? liveEmotionId
    : liveEmotionId;

  const displayAgentVad = resolveDisplayAgentVad(
    liveAgentVad,
    displayEmotionId,
    affectLock.agentVad.locked,
  );

  return (
    <div className="space-y-4">
      <p className="text-[10px] text-muted-foreground">
        点击行末锁图标可锁定测试状态，刷新页面后恢复
      </p>

      {focusedRoundLabel ? (
        <p className="text-[10px] font-medium text-muted-foreground">{focusedRoundLabel}</p>
      ) : null}

      <GuideCardGroup
        accent="amber"
        refPanel={
          <RelationshipStageRefPanel
            currentId={displayStageId}
            affectLock={affectLock.relationship}
            onToggleLock={(refId) => onToggleAffectLock("relationship", refId)}
          />
        }
      >
        <p className="text-xs font-medium text-foreground">关系</p>
        <div className="mt-2">
          <RelationshipMeters relationship={rel} compact hideStage />
        </div>
      </GuideCardGroup>

      <GuideCardGroup
        accent="sky"
        refPanel={
          <EmotionPrototypeRefPanel
            currentId={displayEmotionId}
            estimateLabel={agentMood?.isEstimate ? agentMood.mood.label : null}
            estimateTone={agentMood?.mood.tone}
            isEstimate={agentMood?.isEstimate}
            affectLock={affectLock.agentVad}
            onToggleLock={(refId) => onToggleAffectLock("agent_vad", refId)}
          />
        }
      >
        <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
          <Bot className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
          助手
        </p>
        <div className="mt-2 space-y-2">
          {displayAgentVad ? (
            <VadCompactBlock
              title="VAD"
              accentClass="bg-sky-500/[0.05]"
              point={displayAgentVad}
            />
          ) : (
            <p className="text-[11px] text-muted-foreground">暂无 VAD 数据</p>
          )}
          {attitude ? (
            <p className="text-[11px] text-muted-foreground">
              <span className="text-foreground/85">态度 </span>
              {attitude}
            </p>
          ) : null}
          {agentMood?.intensity && !agentMood.isEstimate ? (
            <p className="text-[11px] text-muted-foreground">
              <span className="text-foreground/85">强度 </span>
              {agentMood.intensity}
            </p>
          ) : null}
        </div>
      </GuideCardGroup>
    </div>
  );
}
