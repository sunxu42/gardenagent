import { useEffect, useState } from "react";
import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiPlanCellClass } from "./a2uiAppleClasses";

const SELECTED_PLAN_PATH = "/selectedPlan";

export function PlanOptionCard({
  component,
  dataModel,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const planId = String(resolveValue(component.planId as string | undefined, ""));
  const title = String(resolveValue(component.title as string | undefined, ""));
  const description = String(resolveValue(component.description as string | undefined, ""));
  const [isSelected, setIsSelected] = useState(false);

  useEffect(() => {
    const syncSelected = () => {
      setIsSelected(dataModel.get(SELECTED_PLAN_PATH) === planId);
    };
    syncSelected();
    return dataModel.subscribe(SELECTED_PLAN_PATH, syncSelected);
  }, [dataModel, planId]);

  const handleSelect = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;

    if (!action?.event || !planId) {
      return;
    }

    dataModel.set(SELECTED_PLAN_PATH, planId);
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: {
        planId,
        ...(title ? { planLabel: title } : {}),
        ...(description ? { planDescription: description } : {}),
        ...action.event.context,
      },
      timestamp: new Date().toISOString(),
    });
  };

  if (!planId || !title) {
    return null;
  }

  return (
    <Button
      type="button"
      variant="ghost"
      onClick={handleSelect}
      aria-pressed={isSelected}
      className={cn(
        a2uiPlanCellClass,
        "h-auto justify-start rounded-none font-normal shadow-none hover:bg-[var(--a2ui-cell-hover)]",
        isSelected && "bg-[var(--a2ui-accent-soft)] hover:bg-[var(--a2ui-accent-soft)]",
      )}
    >
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block text-[0.9375rem] font-medium leading-snug tracking-[-0.01em]",
            isSelected ? "text-[var(--a2ui-accent)]" : "text-[var(--a2ui-title)]",
          )}
        >
          {title}
        </span>
        {description ? (
          <span className="mt-0.5 block text-[0.8125rem] leading-relaxed text-[var(--a2ui-caption)]">
            {description}
          </span>
        ) : null}
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
