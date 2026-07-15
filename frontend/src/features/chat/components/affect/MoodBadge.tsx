import { Cloud, Frown, Meh, Smile, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { MoodTone } from "../../lib/affectPresentation";
import { moodToneClasses } from "../../lib/affectPresentation";
import { cn } from "@/lib/utils";

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
    <Badge
      variant="outline"
      className={cn("max-w-full gap-1.5 rounded-full font-medium shadow-none", pad, styles.badge)}
    >
      <MoodIcon tone={tone} />
      <span className="truncate">{label}</span>
      {sublabel ? <span className="truncate font-normal opacity-75">· {sublabel}</span> : null}
    </Badge>
  );
}

export function EmptyMoodHint() {
  return (
    <Badge
      variant="outline"
      className="gap-1.5 rounded-full border-dashed px-2.5 py-1 text-xs font-normal text-muted-foreground shadow-none"
    >
      <Cloud className="h-3.5 w-3.5" aria-hidden />
      等待对话
    </Badge>
  );
}
