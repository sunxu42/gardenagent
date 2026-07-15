import { useId, type ReactNode } from "react";

import { railCheckboxRowClass } from "@/components/rail/railButtonStyles";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

export interface RailCheckboxFieldProps {
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (checked: boolean) => void;
  children: ReactNode;
  className?: string;
  id?: string;
}

/** Multi-select row backed by shadcn Checkbox. */
export function RailCheckboxField({
  checked,
  disabled = false,
  onCheckedChange,
  children,
  className,
  id: idProp,
}: RailCheckboxFieldProps): JSX.Element {
  const autoId = useId();
  const id = idProp ?? autoId;

  return (
    <label
      htmlFor={id}
      className={cn(
        railCheckboxRowClass(checked),
        "flex w-full cursor-pointer gap-2.5 px-3 py-2.5 text-left",
        disabled && "cursor-not-allowed opacity-60",
        className,
      )}
    >
      <Checkbox
        id={id}
        checked={checked}
        disabled={disabled}
        onCheckedChange={onCheckedChange}
        className={cn(
          "mt-0.5 h-3.5 w-3.5 rounded border shadow-none",
          checked
            ? "border-primary bg-primary text-primary-foreground"
            : "border-rail-pick-border bg-rail-pick-check data-[state=checked]:bg-primary",
          "[&_svg]:h-2.5 [&_svg]:w-2.5",
        )}
      />
      <span className="min-w-0 flex-1">{children}</span>
    </label>
  );
}
