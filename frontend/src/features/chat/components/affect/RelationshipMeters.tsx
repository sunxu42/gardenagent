import { Heart, Shield } from "lucide-react";
import type { RelationshipSnapshot } from "../../types";
import { percent01, relationshipStageLabel } from "../../lib/affectPresentation";

interface RelationshipMetersProps {
  relationship: RelationshipSnapshot | null;
  compact?: boolean;
}

function MeterBar({
  icon: Icon,
  label,
  value,
  compact,
}: {
  icon: typeof Heart;
  label: string;
  value: number;
  compact?: boolean;
}) {
  const pct = percent01(value);
  return (
    <div className={compact ? "space-y-1" : "space-y-1.5"}>
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="inline-flex items-center gap-1 text-muted-foreground">
          <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
          {label}
        </span>
        <span className="tabular-nums font-medium text-foreground">{pct}%</span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} ${pct}%`}
      >
        <div
          className="h-full rounded-full bg-primary/80 transition-[width] duration-300 ease-out motion-reduce:transition-none"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function RelationshipMeters({ relationship, compact }: RelationshipMetersProps) {
  if (!relationship) {
    return (
      <p className="text-xs text-muted-foreground">暂无关系数据</p>
    );
  }

  return (
    <div className={compact ? "space-y-2" : "space-y-3"}>
      <p className="text-xs font-medium text-foreground">
        关系阶段：
        <span className="ml-1 text-primary">{relationshipStageLabel(relationship.stage)}</span>
      </p>
      <MeterBar icon={Shield} label="信任" value={relationship.trust} compact={compact} />
      <MeterBar icon={Heart} label="亲近" value={relationship.warmth} compact={compact} />
    </div>
  );
}
