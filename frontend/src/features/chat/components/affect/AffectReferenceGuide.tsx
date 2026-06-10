import { useState } from "react";
import { VadDimensionGuide } from "./VadDimensionGuide";
import { VadRadarChart } from "../VadRadarChart";
import {
  EMOTION_PROTOTYPES,
  RELATIONSHIP_STAGE_REFS,
  emotionDisplayLabel,
  formatEmotionVad,
} from "../../lib/emotionReference";
import { moodToneClasses } from "../../lib/affectPresentation";

type RefTab = "vad" | "emotions" | "relationship";

const TABS: { id: RefTab; label: string }[] = [
  { id: "vad", label: "V/A/D" },
  { id: "emotions", label: "七种情绪" },
  { id: "relationship", label: "关系" },
];

export function AffectReferenceGuide() {
  const [tab, setTab] = useState<RefTab>("vad");
  const [selectedEmotion, setSelectedEmotion] = useState(EMOTION_PROTOTYPES[0]?.id ?? "neutral");
  const activeProto = EMOTION_PROTOTYPES.find((e) => e.id === selectedEmotion) ?? EMOTION_PROTOTYPES[0];

  return (
    <div className="space-y-3">
      <div
        className="flex gap-0.5 rounded-lg border border-border/35 bg-muted/20 p-0.5"
        role="tablist"
        aria-label="概念参考"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 cursor-pointer rounded-md px-2 py-1 text-[11px] font-medium transition-colors duration-200 ${
              tab === t.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "vad" ? (
        <div role="tabpanel">
          <VadDimensionGuide />
        </div>
      ) : null}

      {tab === "emotions" ? (
        <div role="tabpanel" className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
            <ul className="min-w-0 flex-1 space-y-0.5">
              {EMOTION_PROTOTYPES.map((emo) => {
                const selected = emo.id === selectedEmotion;
                const tone = moodToneClasses(
                  emo.id === "happy" || emo.id === "surprised"
                    ? "positive"
                    : emo.id === "sad"
                      ? "negative"
                      : emo.id === "angry" || emo.id === "fear"
                        ? "tense"
                        : "neutral",
                );
                return (
                  <li key={emo.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedEmotion(emo.id)}
                      className={`w-full cursor-pointer rounded-md px-2.5 py-2 text-left transition-colors duration-200 ${
                        selected ? "bg-primary/10 text-foreground" : "hover:bg-muted/30"
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${tone.dot}`} aria-hidden />
                        <span className="text-xs font-medium">{emotionDisplayLabel(emo.id)}</span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {formatEmotionVad(emo.id)}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
            {activeProto ? (
              <div className="flex shrink-0 flex-col items-center rounded-md bg-muted/20 px-3 py-3">
                <VadRadarChart
                  size={96}
                  showLabels
                  className="text-border"
                  layers={[
                    {
                      point: activeProto.vad,
                      stroke: "#6366f1",
                      fill: "#6366f1",
                      fillOpacity: 0.2,
                      strokeWidth: 2,
                    },
                  ]}
                />
                <p className="mt-2 text-xs font-medium">{emotionDisplayLabel(activeProto.id)}</p>
              </div>
            ) : null}
          </div>
          {activeProto ? (
            <p className="rounded-md bg-muted/20 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
              {activeProto.expression}
            </p>
          ) : null}
        </div>
      ) : null}

      {tab === "relationship" ? (
        <div role="tabpanel" className="space-y-2">
          {RELATIONSHIP_STAGE_REFS.map((stage) => (
            <article key={stage.id} className="rounded-md bg-muted/20 px-3 py-2.5">
              <div className="flex flex-wrap items-baseline gap-x-2">
                <h5 className="text-xs font-medium text-foreground">{stage.label}</h5>
                <span className="text-[10px] text-muted-foreground">{stage.criteria}</span>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                {stage.expression}
              </p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
