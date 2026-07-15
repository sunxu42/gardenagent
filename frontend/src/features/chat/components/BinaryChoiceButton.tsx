import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiApplePressable, a2uiOptionTextWrap } from "./a2uiAppleClasses";

export function BinaryChoiceButton({
  component,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const choiceId = String(resolveValue(component.choiceId as string | undefined, ""));
  const label = String(resolveValue(component.label as string | undefined, ""));
  const variant = String(resolveValue(component.variant as string | undefined, "primary"));
  const isPrimary = variant === "primary";

  const handleSelect = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;
    if (!action?.event || !choiceId) {
      return;
    }
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: action.event.context ?? { choiceId },
      timestamp: new Date().toISOString(),
    });
  };

  if (!choiceId || !label) {
    return null;
  }

  return (
    <Button
      type="button"
      variant={isPrimary ? "default" : "secondary"}
      onClick={handleSelect}
      className={cn(
        "a2ui-binary-segment h-auto min-w-0 flex-1 rounded-[0.5rem] px-4 py-2.5 text-[0.9375rem] font-semibold tracking-[-0.01em] shadow-sm",
        a2uiApplePressable,
        a2uiOptionTextWrap,
        isPrimary
          ? "bg-[var(--a2ui-accent)] text-white hover:bg-[var(--a2ui-accent)] hover:brightness-105"
          : "bg-[var(--a2ui-cell-bg)] text-[var(--a2ui-title)] hover:bg-[var(--a2ui-cell-hover)]",
      )}
    >
      {label}
    </Button>
  );
}
