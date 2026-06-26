import type { ComponentProps, ReactNode } from "react";

import { railInteractiveClass } from "@/components/rail/railButtonStyles";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type RailToolbarButtonProps = ComponentProps<typeof Button> & {
  pressed?: boolean;
  icon?: ReactNode;
};

export function RailToolbarButton({
  pressed,
  icon,
  children,
  className,
  variant,
  size = "rail",
  type = "button",
  ...props
}: RailToolbarButtonProps): JSX.Element {
  return (
    <Button
      type={type}
      variant={variant ?? (pressed ? "rail-active" : "rail")}
      size={size}
      aria-pressed={pressed}
      className={cn(railInteractiveClass, className)}
      {...props}
    >
      {icon ? (
        <span className="inline-flex shrink-0" aria-hidden>
          {icon}
        </span>
      ) : null}
      {children}
    </Button>
  );
}
