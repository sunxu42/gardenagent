import { Bot, User } from "lucide-react";
import type { VadPoint } from "../../types";
import type { SourceItem } from "../../lib/affectSources";
import type { MoodPresentation } from "../../lib/affectPresentation";
import { MoodBadge } from "./MoodBadge";
import { VadDimensionBars } from "./VadDimensionBars";
import { VadRadarChart, type VadRadarLayer } from "../VadRadarChart";
import { AffectSourceList } from "./AffectSourceList";

interface AffectTrackPanelProps {
  variant: "user" | "agent";
  title: string;
  subtitle: string;
  mood: MoodPresentation | null;
  moodSublabel?: string;
  vad: VadPoint | null;
  vadCompare?: VadPoint | null;
  secondaryVad?: VadPoint | null;
  secondaryLabel?: string;
  sources: SourceItem[];
  pending?: boolean;
}

export function AffectTrackPanel({
  variant,
  title,
  subtitle,
  mood,
  moodSublabel,
  vad,
  vadCompare,
  secondaryVad,
  secondaryLabel,
  sources,
  pending,
}: AffectTrackPanelProps) {
  const Icon = variant === "user" ? User : Bot;
  const accent = variant === "user" ? "border-violet-500/25 bg-violet-500/5" : "border-primary/25 bg-primary/5";

  const layers: VadRadarLayer[] = [];
  if (vad) {
    layers.push({
      point: vad,
      stroke: variant === "user" ? "#8b5cf6" : "#3b82f6",
      fill: variant === "user" ? "#8b5cf6" : "#3b82f6",
      fillOpacity: 0.2,
      strokeWidth: 2,
    });
  }
  if (secondaryVad) {
    layers.push({
      point: secondaryVad,
      stroke: "#ef4444",
      fill: "#ef4444",
      fillOpacity: 0.14,
      strokeWidth: 2,
    });
  }

  return (
    <section className={`rounded-xl border p-3 ${accent}`}>
      <div className="mb-3 flex items-start gap-2">
        <span
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
            variant === "user" ? "bg-violet-500/15 text-violet-700 dark:text-violet-200" : "bg-primary/15 text-primary"
          }`}
        >
          <Icon className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-foreground">{title}</h4>
          <p className="text-[11px] leading-snug text-muted-foreground">{subtitle}</p>
        </div>
      </div>

      {pending ? (
        <p className="mb-3 text-xs text-muted-foreground">正在分析…</p>
      ) : null}

      {mood ? (
        <div className="mb-3">
          <MoodBadge label={mood.label} tone={mood.tone} sublabel={moodSublabel} />
        </div>
      ) : null}

      {vad ? (
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start">
          <VadRadarChart size={112} layers={layers} showLabels className="mx-auto shrink-0 text-border sm:mx-0" />
          <div className="min-w-0 flex-1">
            <VadDimensionBars point={vad} compare={vadCompare} />
            {secondaryVad && secondaryLabel ? (
              <p className="mt-2 text-[10px] text-muted-foreground">
                <span className="inline-block h-2 w-2 rounded-full bg-red-500 align-middle" /> {secondaryLabel}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      <AffectSourceList items={sources} />
    </section>
  );
}
