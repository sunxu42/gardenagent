import type { ComponentProps, ReactNode } from "react";

import { railInteractiveClass, railTabListClass } from "@/components/rail/railButtonStyles";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface RailTabListProps {
  "aria-label": string;
  children: ReactNode;
  className?: string;
}

export function RailTabList({ "aria-label": ariaLabel, children, className }: RailTabListProps): JSX.Element {
  return (
    <nav aria-label={ariaLabel} className={cn(railTabListClass, className)} role="tablist">
      {children}
    </nav>
  );
}

export type RailTabProps = ComponentProps<typeof Button> & {
  selected: boolean;
};

export function RailTab({
  selected,
  children,
  className,
  variant,
  size = "rail",
  type = "button",
  ...props
}: RailTabProps): JSX.Element {
  return (
    <Button
      type={type}
      role="tab"
      aria-selected={selected}
      variant={variant ?? (selected ? "rail-active" : "rail")}
      size={size}
      className={cn(railInteractiveClass, "rounded", className)}
      {...props}
    >
      {children}
    </Button>
  );
}

export type RailChipButtonProps = ComponentProps<typeof Button> & {
  selected?: boolean;
};

export function RailChipButton({
  selected,
  className,
  variant,
  size = "rail-chip",
  type = "button",
  ...props
}: RailChipButtonProps): JSX.Element {
  return (
    <Button
      type={type}
      aria-pressed={selected}
      variant={variant ?? (selected ? "rail-active" : "rail")}
      size={size}
      className={cn(railInteractiveClass, className)}
      {...props}
    />
  );
}

export type RailListItemButtonProps = ComponentProps<typeof Button> & {
  selected?: boolean;
};

export function RailListItemButton({
  selected,
  className,
  variant,
  size = "rail-list",
  type = "button",
  ...props
}: RailListItemButtonProps): JSX.Element {
  return (
    <Button
      type={type}
      aria-pressed={selected}
      variant={variant ?? (selected ? "rail-list-active" : "rail-list")}
      size={size}
      className={cn(railInteractiveClass, className)}
      {...props}
    />
  );
}
