import { cn } from "@/lib/utils";

/** Segmented tab list container (pill group). */
export const railTabListClass =
  "inline-flex shrink-0 gap-0.5 rounded-md bg-rail-track p-0.5";

/** Shared interactive class for reduced-motion overrides. */
export const railInteractiveClass = "rail-interactive";

/** Selectable row — scenario checkbox (warmer tan). */
export function railCheckboxRowClass(selected: boolean, className?: string): string {
  return cn(
    railInteractiveClass,
    "rounded-md border transition-colors duration-200",
    selected
      ? "border-rail-pick-border-active bg-rail-pick-active"
      : "border-rail-pick-border bg-rail-pick hover:bg-rail-pick-hover",
    className,
  );
}

/** Selectable row — history listbox (deeper brown). */
export function railHistoryRowClass(selected: boolean, className?: string): string {
  return cn(
    railInteractiveClass,
    "rounded-md border transition-colors duration-200",
    selected
      ? "border-rail-history-border-active bg-rail-history-active"
      : "border-rail-history-border bg-rail-history hover:bg-rail-history-hover",
    className,
  );
}

/** Small checkbox-style indicator inside scenario rows. */
export function railListCheckClass(checked: boolean, className?: string): string {
  return cn(
    "mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border transition-colors duration-200",
    checked
      ? "border-primary/50 bg-primary/15 text-primary"
      : "border-rail-pick-border bg-rail-pick-check",
    className,
  );
}
