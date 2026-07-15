import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import type { AffectTurnRecord } from "../types";
import { formatTimestamp } from "../lib/affectFormat";
import { inferUserMood, resolveAttitudeSummary } from "../lib/affectPresentation";
import { AffectTurnCardDebug } from "./affect/AffectTurnCardDebug";
import { agentRoundDelta, VadCompactBlock } from "./affect/VadCompactBlock";

import "./affect-turn-card.css";

interface AffectTurnCardProps {
  record: AffectTurnRecord;
  prevRecord?: AffectTurnRecord | null;
  index: number;
  total: number;
  devMode: boolean;
}

export function AffectTurnCard({
  record,
  prevRecord,
  index,
  total,
  devMode,
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
  const userMood = inferUserMood(record.userAffectVad);
  const agentDelta = agentRoundDelta(record, prevRecord?.agentVadAfter);
  const roundLabel = `第 ${total - index} 轮`;

  return (
    <li className="affect-turn-list__item">
      <article className="affect-turn-card" aria-label={`${roundLabel}情绪记录`}>
        <header className="affect-turn-card__header">
          <span className="affect-turn-card__round">{roundLabel}</span>
          <time className="affect-turn-card__time" dateTime={new Date(record.createdAt).toISOString()}>
            {formatTimestamp(record.createdAt)}
          </time>
          {isPending ? (
            <span className="affect-turn-card__status">
              <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" aria-hidden />
              感知中
            </span>
          ) : null}
          {settledPending && isPending ? (
            <span className="affect-turn-card__status">回应生成中…</span>
          ) : null}
        </header>

        <p className="affect-turn-card__quote">{record.userText || "（无文字内容）"}</p>

        <div className="affect-turn-card__metrics">
          <VadCompactBlock
            title="用户"
            accentClass="bg-violet-500/[0.06]"
            point={record.userAffectVad}
            footnote={`本轮感知 · ${userMood.label}`}
          />
          <VadCompactBlock
            title="助手"
            accentClass="affect-status-accent"
            point={agentVad}
            roundDelta={agentDelta}
            pending={!agentVad && isPending}
          />
        </div>

        <footer className="affect-turn-card__footer">
          <span>态度 · {attitude}</span>
        </footer>
      </article>

      {devMode ? (
        <div className="affect-turn-card__debug">
          <AffectTurnCardDebug record={record} index={index} total={total} />
        </div>
      ) : null}
    </li>
  );
}
