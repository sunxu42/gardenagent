import type { AffectTurnRecord, VadPoint } from "../../types";
import {
  deltaToneClass,
  formatAffectNum,
  formatTimestamp,
  formatVadTriple,
  shortTurnId,
} from "../../lib/affectFormat";
import { formatVad } from "../../lib/vadRadarUtils";
import { VadRadarChart } from "../VadRadarChart";

interface AffectTurnCardDebugProps {
  record: AffectTurnRecord;
  index: number;
  total: number;
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 font-mono text-[10px]">
      <span className="text-muted-foreground">{label}</span>
      <span className="break-words">{value}</span>
    </div>
  );
}

export function AffectTurnCardDebug({ record, index, total }: AffectTurnCardDebugProps) {
  const isV2 = record.schemaVersion === 2;
  const layers: Array<{
    point: VadPoint;
    stroke: string;
    fill: string;
    fillOpacity: number;
    strokeWidth: number;
  }> = [
    {
      point: record.userAffectVad,
      stroke: "#8b5cf6",
      fill: "#8b5cf6",
      fillOpacity: 0.16,
      strokeWidth: 2,
    },
  ];
  if (record.agentVadTarget) {
    layers.push({
      point: record.agentVadTarget,
      stroke: "#3b82f6",
      fill: "#3b82f6",
      fillOpacity: 0.16,
      strokeWidth: 2,
    });
  }
  if (record.agentVadAfter) {
    layers.push({
      point: record.agentVadAfter,
      stroke: "#ef4444",
      fill: "#ef4444",
      fillOpacity: 0.16,
      strokeWidth: 2.4,
    });
  }

  const deltaLine =
    record.delta && record.agentVadAfter
      ? `${formatVad(record.delta.v)} / ${formatVad(record.delta.a)} / ${formatVad(record.delta.d)}`
      : null;

  return (
    <div className="space-y-2 rounded-md border border-dashed border-border/80 bg-muted/30 p-2">
      <p className="font-mono text-[10px] text-muted-foreground">
        #{total - index} · {formatTimestamp(record.createdAt)} · {shortTurnId(record.turnId)}
      </p>

      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1 space-y-1">
          <FieldRow label="User VAD" value={formatVadTriple(record.userAffectVad)} />
          {isV2 && record.relationship ? (
            <FieldRow
              label="Rel"
              value={`trust ${formatAffectNum(record.relationship.trust)} / warmth ${formatAffectNum(record.relationship.warmth)}`}
            />
          ) : null}
          {record.agentVadTarget ? (
            <FieldRow label="Target" value={formatVadTriple(record.agentVadTarget)} />
          ) : null}
          {record.agentVadAfter ? <FieldRow label="Agent" value={formatVadTriple(record.agentVadAfter)} /> : null}
          {deltaLine ? (
            <FieldRow
              label="Agent Δ"
              value={deltaLine}
            />
          ) : null}
          {record.synthesisRule ? (
            <FieldRow label="Rule" value={record.synthesisRule} />
          ) : null}
        </div>

        <div className="shrink-0 text-center">
          <VadRadarChart size={72} className="text-border" layers={layers} />
          <ul className="mt-1 space-y-0.5 font-mono text-[9px] leading-tight text-muted-foreground">
            <li>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-violet-500 align-middle" /> user
            </li>
            {record.agentVadTarget ? (
              <li>
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 align-middle" /> target
              </li>
            ) : null}
            {record.agentVadAfter ? (
              <li>
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500 align-middle" /> agent
              </li>
            ) : null}
          </ul>
        </div>
      </div>

      {record.delta ? (
        <p className={`font-mono text-[10px] ${deltaToneClass(record.delta.v)}`}>raw payload below</p>
      ) : null}
      <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-all rounded bg-background/80 p-1.5 font-mono text-[10px] text-muted-foreground">
        {JSON.stringify(record, null, 2)}
      </pre>
    </div>
  );
}
