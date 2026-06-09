import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import type { AffectTurnRecord } from "../types";
import { formatTimestamp } from "../lib/affectFormat";
import { resolveAttitudeSummary } from "../lib/affectPresentation";
import { AffectTurnCardDebug } from "./affect/AffectTurnCardDebug";
import { agentRoundDelta, userRoundDelta, VadCompactBlock } from "./affect/VadCompactBlock";

interface AffectTurnCardProps {
  record: AffectTurnRecord;
  prevRecord?: AffectTurnRecord | null;
  index: number;
  total: number;
  devMode: boolean;
  selected?: boolean;
  onSelect?: () => void;
}

export function AffectTurnCard({
  record,
  prevRecord,
  index,
  total,
  devMode,
  selected = false,
  onSelect,
}: AffectTurnCardProps) {
  const [settledPending, setSettledPending] = useState(false);

  useEffect(() => {
    if (record.phase === "settled") {
      setSettledPending(false);
      return;
    }
    const timer = window.setTimeout(() => setSettledPending(true), 5000);
    return () => window.clearTimeout(timer);
  }, [record.phase, record.turnId]);

  const isPending = record.phase !== "settled" && !record.agentVadAfter;
  const agentVad = record.agentVadAfter ?? record.agentVadTarget ?? null;
  const attitude = resolveAttitudeSummary(record);

  const userDelta = userRoundDelta(record.userAffectVad, prevRecord?.userAffectVad);
  const agentDelta = agentRoundDelta(record, prevRecord?.agentVadAfter);

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={`w-full cursor-pointer rounded-md border px-3 py-2 text-left transition-colors duration-200 ${
          selected
            ? "border-border bg-muted/35"
            : "border-transparent bg-transparent hover:bg-muted/25"
        }`}
        aria-pressed={selected}
        aria-label={`第 ${total - index} 轮情绪记录，点击查看说明`}
      >
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <span className="text-xs font-medium text-muted-foreground">第 {total - index} 轮</span>
          <span className="text-[10px] text-muted-foreground">{formatTimestamp(record.createdAt)}</span>
          {isPending ? (
            <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" aria-hidden />
              感知中
            </span>
          ) : null}
          {settledPending && isPending ? (
            <span className="text-[10px] text-muted-foreground">回应生成中…</span>
          ) : null}
        </div>

        <p className="mt-1 line-clamp-2 text-[11px] leading-snug text-muted-foreground">
          {record.userText || "（无文字内容）"}
        </p>

        <div className="mt-2 grid gap-1.5">
          <VadCompactBlock
            title="用户"
            accentClass="border-border/30 bg-muted/15"
            point={record.userAffectVad}
            roundDelta={userDelta}
          />
          <VadCompactBlock
            title="助手"
            accentClass="border-border/30 bg-muted/15"
            point={agentVad}
            roundDelta={agentDelta}
            pending={!agentVad && isPending}
          />
        </div>

        <p className="mt-2 text-[11px] leading-snug">
          <span className="text-muted-foreground">态度 </span>
          <span className="text-muted-foreground">{attitude}</span>
        </p>
      </button>

      {devMode ? (
        <div className="mt-1 rounded-xl border border-dashed border-border/60 bg-muted/20 px-3 py-2">
          <AffectTurnCardDebug record={record} index={index} total={total} />
        </div>
      ) : null}
    </li>
  );
}
