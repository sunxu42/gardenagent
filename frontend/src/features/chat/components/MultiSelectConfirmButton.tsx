import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiApplePressable } from "./a2uiAppleClasses";

const SELECTED_IDS_PATH = "/selectedIds";

export function MultiSelectConfirmButton({
  component,
  dataModel,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const label = String(resolveValue(component.text as string | undefined, "确认选择"));

  const handleConfirm = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;
    if (!action?.event) {
      return;
    }
    const current = dataModel.get(SELECTED_IDS_PATH);
    const selectedIds = Array.isArray(current) ? current.map(String) : [];
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: action.event.context ?? { selectedIds },
      timestamp: new Date().toISOString(),
    });
  };

  return (
    <Button
      type="button"
      onClick={handleConfirm}
      className={cn(
        "a2ui-confirm-btn mt-1 h-auto w-full rounded-xl bg-[var(--a2ui-accent)] px-4 py-3",
        "text-[0.9375rem] font-semibold tracking-[-0.01em] text-white shadow-sm",
        "hover:bg-[var(--a2ui-accent)] hover:brightness-105",
        a2uiApplePressable,
      )}
    >
      {label}
    </Button>
  );
}
