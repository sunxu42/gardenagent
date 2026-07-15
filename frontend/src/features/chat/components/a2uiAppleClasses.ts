import { cn } from "@/lib/utils";

/** Override shadcn Button `whitespace-nowrap` for multi-line option labels. */
export const a2uiOptionTextWrap = "whitespace-normal break-words [overflow-wrap:anywhere]";

/** Shared press feedback for Apple-style interactive cells. */
export const a2uiApplePressable = cn(
  "cursor-pointer transition-[background-color,transform,box-shadow,color] duration-200 ease-out",
  "active:scale-[0.985]",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--a2ui-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--a2ui-group-bg)]",
);

export const a2uiPlanCellClass = cn(
  "a2ui-plan-cell group relative flex w-full items-start gap-3 px-4 py-3.5 text-left",
  "bg-[var(--a2ui-cell-bg)] hover:bg-[var(--a2ui-cell-hover)]",
  a2uiApplePressable,
  a2uiOptionTextWrap,
);

export const a2uiMultiCellClass = cn(
  "a2ui-multi-cell group relative flex w-full items-start gap-3 px-4 py-3.5 text-left",
  "bg-[var(--a2ui-cell-bg)] hover:bg-[var(--a2ui-cell-hover)]",
  a2uiApplePressable,
  a2uiOptionTextWrap,
);
