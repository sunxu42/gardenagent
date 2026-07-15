import { useEffect, useState } from "react";
import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiMultiCellClass } from "./a2uiAppleClasses";

const SELECTED_IDS_PATH = "/selectedIds";

export function MultiSelectOption({
  component,
  dataModel,
  resolveValue,
}: ComponentAdapterProps) {
  const optionId = String(resolveValue(component.optionId as string | undefined, ""));
  const label = String(resolveValue(component.label as string | undefined, ""));
  const description = String(resolveValue(component.description as string | undefined, ""));
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const sync = () => {
      const current = dataModel.get(SELECTED_IDS_PATH);
      const ids = Array.isArray(current) ? current.map(String) : [];
      setChecked(ids.includes(optionId));
    };
    sync();
    return dataModel.subscribe(SELECTED_IDS_PATH, sync);
  }, [dataModel, optionId]);

  const toggle = () => {
    const current = dataModel.get(SELECTED_IDS_PATH);
    const ids = Array.isArray(current) ? current.map(String) : [];
    const next = checked ? ids.filter((id) => id !== optionId) : [...ids, optionId];
    dataModel.set(SELECTED_IDS_PATH, next);
  };

  if (!optionId || !label) {
    return null;
  }

  return (
    <Button
      type="button"
      variant="ghost"
      role="checkbox"
      aria-checked={checked}
      onClick={toggle}
      className={cn(
        a2uiMultiCellClass,
        "h-auto justify-start rounded-none font-normal shadow-none hover:bg-[var(--a2ui-cell-hover)]",
        checked && "bg-[var(--a2ui-accent-soft)] hover:bg-[var(--a2ui-accent-soft)]",
      )}
    >
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block text-[0.9375rem] font-medium leading-snug tracking-[-0.01em]",
            checked ? "text-[var(--a2ui-accent)]" : "text-[var(--a2ui-title)]",
          )}
        >
          {label}
        </span>
        {description ? (
          <span className="mt-0.5 block text-[0.8125rem] leading-relaxed text-[var(--a2ui-caption)]">
            {description}
          </span>
        ) : null}
      </span>
      <span
        className={cn(
          "flex h-[1.375rem] w-[1.375rem] shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-200",
          checked
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
