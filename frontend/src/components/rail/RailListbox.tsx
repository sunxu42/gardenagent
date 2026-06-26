import type { KeyboardEvent, ReactNode } from "react";

import { railHistoryRowClass } from "@/components/rail/railButtonStyles";
import { cn } from "@/lib/utils";

export interface RailListboxProps {
  "aria-label": string;
  children: ReactNode;
  className?: string;
}

/** Single-select list container (WAI-ARIA listbox). */
export function RailListbox({ "aria-label": ariaLabel, children, className }: RailListboxProps): JSX.Element {
  return (
    <ul aria-label={ariaLabel} className={cn("m-0 list-none space-y-1.5 p-0", className)} role="listbox">
      {children}
    </ul>
  );
}

export interface RailListboxOptionProps {
  selected: boolean;
  onSelect: () => void;
  children: ReactNode;
  className?: string;
}

/** Single-select row (role=option, not a button). */
export function RailListboxOption({
  selected,
  onSelect,
  children,
  className,
}: RailListboxOptionProps): JSX.Element {
  const handleKeyDown = (event: KeyboardEvent<HTMLLIElement>): void => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  };

  return (
    <li
      role="option"
      aria-selected={selected}
      tabIndex={selected ? 0 : -1}
      className={cn(
        railHistoryRowClass(selected),
        "block w-full cursor-pointer px-3 py-2.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        className,
      )}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
    >
      {children}
    </li>
  );
}
