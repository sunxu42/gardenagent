import type { VadPoint } from "../../types";
import { computeVadDelta } from "../../lib/affectMerge";
import { deltaToneClass, formatAffectNum } from "../../lib/affectFormat";

interface VadCompactBlockProps {
  title: string;
  accentClass: string;
  point: VadPoint | null;
  /** 相对上一轮状态机的变化（仅助手侧） */
  roundDelta?: VadPoint | null;
  /** 无 roundDelta 时的说明行（如用户侧「本轮感知」） */
  footnote?: string;
  pending?: boolean;
  /** 素雅模式：Δ 不用红绿强调 */
  subdued?: boolean;
}

function formatDelta(n: number): string {
  if (!Number.isFinite(n) || Math.abs(n) < 0.005) return "0";
  const sign = n > 0 ? "+" : "";
  return `${sign}${formatAffectNum(n)}`;
}

function DeltaCell({ label, value, subdued }: { label: string; value: number; subdued?: boolean }) {
  return (
    <span className={`font-mono text-[10px] ${subdued ? "text-muted-foreground/80" : deltaToneClass(value)}`}>
      {label} {formatDelta(value)}
    </span>
  );
}

export function VadCompactBlock({
  title,
  accentClass,
  point,
  roundDelta,
  footnote,
  pending,
  subdued,
}: VadCompactBlockProps) {
  if (pending) {
    return (
      <div className={`rounded-md px-2 py-1.5 ${accentClass}`}>
        <p className="text-[10px] font-medium text-muted-foreground">{title}</p>
        <p className="mt-0.5 text-[10px] text-muted-foreground">等待中…</p>
      </div>
    );
  }

  if (!point) {
    return (
      <div className={`rounded-md px-2 py-1.5 ${accentClass}`}>
        <p className="text-[10px] font-medium text-muted-foreground">{title}</p>
        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">—</p>
      </div>
    );
  }

  return (
    <div className={`rounded-md px-2 py-1.5 ${accentClass}`}>
      <p className="text-[10px] font-medium text-muted-foreground">{title}</p>
      <p className="mt-0.5 font-mono text-[11px] leading-relaxed text-muted-foreground">
        V {formatAffectNum(point.v)} · A {formatAffectNum(point.a)} · D {formatAffectNum(point.d)}
      </p>
      {roundDelta ? (
        <p className="mt-0.5 flex flex-wrap gap-x-2 gap-y-0">
          <span className="text-[10px] text-muted-foreground">相对上轮</span>
          <DeltaCell label="V" value={roundDelta.v} subdued={subdued} />
          <DeltaCell label="A" value={roundDelta.a} subdued={subdued} />
          <DeltaCell label="D" value={roundDelta.d} subdued={subdued} />
        </p>
      ) : footnote ? (
        <p className="mt-0.5 text-[10px] text-muted-foreground">{footnote}</p>
      ) : (
        <p className="mt-0.5 text-[10px] text-muted-foreground">相对上轮 · 首轮或无对比</p>
      )}
    </div>
  );
}

export function agentRoundDelta(
  record: { agentVadAfter?: VadPoint; delta?: VadPoint },
  prevAgent: VadPoint | null | undefined,
): VadPoint | null {
  if (record.delta && record.agentVadAfter) return record.delta;
  if (record.agentVadAfter && prevAgent) {
    return computeVadDelta(record.agentVadAfter, prevAgent);
  }
  return null;
}
