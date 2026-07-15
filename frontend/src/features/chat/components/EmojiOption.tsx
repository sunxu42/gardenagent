import { useEffect, useState } from "react";
import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiApplePressable, a2uiOptionTextWrap } from "./a2uiAppleClasses";

const SELECTED_EMOJI_PATH = "/selectedEmoji";

export const a2uiEmojiCellClass = cn(
  "a2ui-emoji-cell group relative flex w-full items-start gap-3 px-4 py-3.5 text-left",
  "bg-[var(--a2ui-cell-bg)] hover:bg-[var(--a2ui-cell-hover)]",
  a2uiApplePressable,
  a2uiOptionTextWrap,
);

export function EmojiOption({
  component,
  dataModel,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const optionId = String(resolveValue(component.optionId as string | undefined, ""));
  const emoji = String(resolveValue(component.emoji as string | undefined, ""));
  const label = String(resolveValue(component.label as string | undefined, ""));
  const [isSelected, setIsSelected] = useState(false);

  useEffect(() => {
    const syncSelected = () => {
      setIsSelected(dataModel.get(SELECTED_EMOJI_PATH) === optionId);
    };
    syncSelected();
    return dataModel.subscribe(SELECTED_EMOJI_PATH, syncSelected);
  }, [dataModel, optionId]);

  const handleSelect = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;

    if (!action?.event || !optionId) {
      return;
    }

    dataModel.set(SELECTED_EMOJI_PATH, optionId);
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: action.event.context ?? { optionId, emoji },
      timestamp: new Date().toISOString(),
    });
  };

  if (!optionId || !label) {
    return null;
  }

  return (
    <Button
      type="button"
      variant="ghost"
      onClick={handleSelect}
      aria-pressed={isSelected}
      className={cn(
        a2uiEmojiCellClass,
        "h-auto justify-start rounded-none font-normal shadow-none hover:bg-[var(--a2ui-cell-hover)]",
        isSelected && "bg-[var(--a2ui-accent-soft)] hover:bg-[var(--a2ui-accent-soft)]",
      )}
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center text-2xl leading-none" aria-hidden>
        {emoji || "🙂"}
      </span>
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block text-[0.9375rem] font-medium leading-snug tracking-[-0.01em]",
            isSelected ? "text-[var(--a2ui-accent)]" : "text-[var(--a2ui-title)]",
          )}
        >
          {label}
        </span>
      </span>
      <span
        className={cn(
          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors duration-200",
          isSelected
            ? "border-[var(--a2ui-accent)] bg-[var(--a2ui-accent)] text-white"
            : "border-[var(--a2ui-separator)] bg-transparent text-transparent",
        )}
        aria-hidden
      >
        <Check className="h-3 w-3" strokeWidth={3} />
      </span>
    </Button>
  );
}
