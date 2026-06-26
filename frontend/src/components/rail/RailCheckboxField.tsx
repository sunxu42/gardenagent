import { Check } from "lucide-react";
import { useId, type ReactNode } from "react";

import { railCheckboxRowClass, railListCheckClass } from "@/components/rail/railButtonStyles";
import { cn } from "@/lib/utils";

export interface RailCheckboxFieldProps {
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (checked: boolean) => void;
  children: ReactNode;
  className?: string;
  id?: string;
}

/** Multi-select row: native checkbox + label (not a button). */
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
      <input
        id={id}
        type="checkbox"
        checked={checked}
        disabled={disabled}
        className="sr-only"
        onChange={(event) => onCheckedChange(event.target.checked)}
      />
      <span className={railListCheckClass(checked)} aria-hidden>
        {checked ? <Check className="h-2.5 w-2.5" strokeWidth={3} /> : null}
      </span>
      <span className="min-w-0 flex-1">{children}</span>
    </label>
  );
}
