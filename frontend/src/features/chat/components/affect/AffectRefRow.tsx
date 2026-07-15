import { Lock, LockOpen } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface AffectRefRowProps {
  current?: boolean;
  locked?: boolean;
  accent?: "amber" | "sky";
  onToggleLock?: () => void;
  children: ReactNode;
}

const CURRENT_BORDER: Record<NonNullable<AffectRefRowProps["accent"]>, string> = {
  amber: "border-amber-500/30",
  sky: "border-sky-500/30",
};

export function AffectRefRow({
  current = false,
  locked = false,
  accent = "amber",
  onToggleLock,
  children,
}: AffectRefRowProps) {
  const borderClass = current ? CURRENT_BORDER[accent] : "border-transparent";
  const LockIcon = locked ? Lock : LockOpen;

  return (
    <div className={`rounded-md border px-2.5 py-2 ${borderClass}`}>
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">{children}</div>
        {onToggleLock ? (
          <div className="flex shrink-0 items-center gap-1 self-start pt-0.5">
            {locked ? (
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400">已锁定</span>
            ) : null}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onToggleLock}
              aria-label={locked ? "解锁" : "锁定"}
              aria-pressed={locked}
              className="h-6 w-6 shrink-0 rounded-md shadow-none hover:bg-transparent"
            >
              <LockIcon
                className={`h-3.5 w-3.5 ${
                  locked
                    ? "fill-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                    : "text-muted-foreground/70"
                }`}
                aria-hidden
              />
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
