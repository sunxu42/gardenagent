import type { MoodTone } from "../../lib/affectPresentation";
import { moodToneClasses } from "../../lib/affectPresentation";
import {
  DEFAULT_AGENT_EMOTION_ID,
  EMOTION_PROTOTYPES,
  emotionDisplayLabel,
  emotionToneDotClass,
  formatEmotionVad,
} from "../../lib/emotionReference";
import type { AffectLockSlice } from "../../types";
import { AffectRefReorderPanel } from "./AffectRefReorderPanel";
import { AffectRefRow } from "./AffectRefRow";

interface EmotionPrototypeRefPanelProps {
  currentId?: string | null;
  estimateLabel?: string | null;
  estimateTone?: MoodTone;
  isEstimate?: boolean;
  affectLock?: AffectLockSlice;
  onToggleLock?: (refId: string) => void;
}

export function EmotionPrototypeRefPanel({
  currentId = DEFAULT_AGENT_EMOTION_ID,
  estimateLabel,
  estimateTone = "neutral",
  isEstimate,
  affectLock,
  onToggleLock,
}: EmotionPrototypeRefPanelProps) {
  const resolvedId = currentId ?? DEFAULT_AGENT_EMOTION_ID;
  const proto = EMOTION_PROTOTYPES.find((e) => e.id === resolvedId);

  if (!proto && estimateLabel) {
    const dot = moodToneClasses(estimateTone).dot;
    return (
      <AffectRefReorderPanel
        items={EMOTION_PROTOTYPES}
        currentId={DEFAULT_AGENT_EMOTION_ID}
        affectLock={affectLock}
        onToggleLock={onToggleLock}
        expandable={EMOTION_PROTOTYPES.length > 1}
        renderItem={(emo, { current, locked, onToggleLock: toggle }) => (
          <AffectRefRow
            current={current}
            accent="sky"
            locked={locked}
            onToggleLock={toggle}
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <span className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                <span
                  className={`h-1.5 w-1.5 shrink-0 rounded-full ${emotionToneDotClass(emo.id)}`}
                  aria-hidden
                />
                {emotionDisplayLabel(emo.id)}
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">{formatEmotionVad(emo.id)}</span>
            </div>
            <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{emo.expression}</p>
          </AffectRefRow>
        )}
      />
    );
  }

  const hasOthers = EMOTION_PROTOTYPES.some((emo) => emo.id !== resolvedId);

  return (
    <AffectRefReorderPanel
      items={EMOTION_PROTOTYPES}
      currentId={resolvedId}
      affectLock={affectLock}
      onToggleLock={onToggleLock}
      expandable={hasOthers}
      emptyState={<p className="text-muted-foreground">暂无情绪数据</p>}
      renderItem={(emo, { current, locked, onToggleLock: toggle }) => (
        <AffectRefRow
          current={current}
          accent="sky"
          locked={locked}
          onToggleLock={toggle}
        >
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="flex items-center gap-1.5 text-xs font-medium text-foreground">
              <span
                className={`h-1.5 w-1.5 shrink-0 rounded-full ${emotionToneDotClass(emo.id)}`}
                aria-hidden
              />
              {emotionDisplayLabel(emo.id)}
            </span>
            <span className="font-mono text-[10px] text-muted-foreground">{formatEmotionVad(emo.id)}</span>
            {current && isEstimate && estimateLabel && emo.id === resolvedId ? (
              <span className="text-[10px] text-muted-foreground">由 VAD 推断</span>
            ) : null}
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{emo.expression}</p>
        </AffectRefRow>
      )}
    />
  );
}
