import type { AffectLockSlice } from "../../types";
import { relationshipStageLabel } from "../../lib/affectPresentation";
import { formatRelationshipPreset, RELATIONSHIP_STAGE_REFS } from "../../lib/emotionReference";
import { AffectRefReorderPanel } from "./AffectRefReorderPanel";
import { AffectRefRow } from "./AffectRefRow";

interface RelationshipStageRefPanelProps {
  currentId?: string | null;
  affectLock?: AffectLockSlice;
  onToggleLock?: (refId: string) => void;
}

export function RelationshipStageRefPanel({
  currentId,
  affectLock,
  onToggleLock,
}: RelationshipStageRefPanelProps) {
  const hasOthers = currentId
    ? RELATIONSHIP_STAGE_REFS.some((stage) => stage.id !== currentId)
    : RELATIONSHIP_STAGE_REFS.length > 0;

  return (
    <AffectRefReorderPanel
      items={RELATIONSHIP_STAGE_REFS}
      currentId={currentId}
      affectLock={affectLock}
      onToggleLock={onToggleLock}
      expandable={hasOthers}
      emptyState={<p className="text-muted-foreground">暂无关系阶段</p>}
      renderItem={(stage, { current, locked, onToggleLock: toggle }) => (
        <AffectRefRow
          current={current}
          accent="amber"
          locked={locked}
          onToggleLock={toggle}
        >
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="text-xs font-medium text-foreground">
              {relationshipStageLabel(stage.id)}
            </span>
            <span className="text-[10px] text-muted-foreground">{stage.criteria}</span>
            <span className="font-mono text-[10px] text-muted-foreground">
              {formatRelationshipPreset(stage.id)}
            </span>
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{stage.expression}</p>
        </AffectRefRow>
      )}
    />
  );
}
