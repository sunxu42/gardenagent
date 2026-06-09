import { Cloud, Frown, Meh, Smile, Zap } from "lucide-react";
import type { MoodTone } from "../../lib/affectPresentation";
import { moodToneClasses } from "../../lib/affectPresentation";

interface MoodBadgeProps {
  label: string;
  tone: MoodTone;
  sublabel?: string;
  size?: "sm" | "md";
}

function MoodIcon({ tone }: { tone: MoodTone }) {
  const className = "h-3.5 w-3.5 shrink-0 opacity-80";
  switch (tone) {
    case "positive":
      return <Smile className={className} aria-hidden />;
    case "negative":
      return <Frown className={className} aria-hidden />;
    case "tense":
      return <Zap className={className} aria-hidden />;
    default:
      return <Meh className={className} aria-hidden />;
  }
}

export function MoodBadge({ label, tone, sublabel, size = "md" }: MoodBadgeProps) {
  const styles = moodToneClasses(tone);
  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex max-w-full items-center gap-1.5 rounded-full border font-medium ${pad} ${styles.badge}`}
    >
      <MoodIcon tone={tone} />
      <span className="truncate">{label}</span>
      {sublabel ? <span className="truncate font-normal opacity-75">· {sublabel}</span> : null}
    </span>
  );
}

export function EmptyMoodHint() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-border px-2.5 py-1 text-xs text-muted-foreground">
      <Cloud className="h-3.5 w-3.5" aria-hidden />
      等待对话
    </span>
  );
}
