import { cn } from "@/lib/utils";

/** Segmented tab list container (pill group). */
export const railTabListClass =
  "inline-flex shrink-0 items-center gap-0.5 rounded-md bg-rail-track p-0.5";

/** Shared interactive class for reduced-motion overrides. */
export const railInteractiveClass = "rail-interactive";

/** Selectable row — scenario checkbox (warm white card + sky lift on hover). */
export function railCheckboxRowClass(selected: boolean, className?: string): string {
  return cn(
    railInteractiveClass,
    "rounded-md border shadow-none transition-[background,border-color,box-shadow] duration-200",
    selected
      ? "border-rail-pick-border border-l-[3px] border-l-primary bg-rail-pick shadow-none"
      : "border-rail-pick-border bg-rail-pick hover:border-rail-pick-border-active/35 hover:bg-rail-pick-hover hover:shadow-[0_1px_3px_hsl(38_20%_20%_/_0.04)]",
    className,
  );
}

/** Selectable row — history listbox. */
export function railHistoryRowClass(selected: boolean, className?: string): string {
  return cn(
    railInteractiveClass,
    "rounded-md border shadow-none transition-[background,border-color,box-shadow] duration-200",
    selected
      ? "border-rail-history-border-active bg-rail-history-active"
      : "border-rail-history-border bg-rail-history hover:border-rail-history-border-active/35 hover:bg-rail-history-hover hover:shadow-[0_1px_3px_hsl(38_20%_20%_/_0.04)]",
    className,
  );
}

/** Small checkbox-style indicator inside scenario rows. */
export function railListCheckClass(checked: boolean, className?: string): string {
  return cn(
    "mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border transition-colors duration-200",
    checked
      ? "border-primary bg-primary text-primary-foreground"
      : "border-rail-pick-border bg-rail-pick-check",
    className,
  );
}
