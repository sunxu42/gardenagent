import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors duration-200 disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        rail: "bg-rail-btn text-rail-fg-muted shadow-none hover:bg-rail-btn-hover hover:text-rail-fg",
        "rail-active":
          "bg-rail-btn-active text-rail-fg shadow-none hover:bg-rail-btn-active-hover",
        "rail-list":
          "border border-rail-border bg-rail-list text-left shadow-none hover:bg-rail-list-hover justify-start",
        "rail-list-active":
          "border border-rail-border-active bg-rail-list-active text-left shadow-none justify-start",
      },
      size: {
        default: "h-10 px-4 py-2",
        icon: "h-10 w-10",
        sm: "h-9 rounded-md px-3",
        rail: "h-auto shrink-0 rounded-md px-2.5 py-1.5 text-[11px] font-medium gap-1.5",
        "rail-chip": "h-auto shrink-0 rounded-md px-2 py-1 text-[10px] font-medium",
        "rail-list": "h-auto w-full rounded-md px-3 py-2.5 text-left font-normal",
        "rail-list-sm": "h-auto w-full rounded-md px-3 py-2 text-left font-normal",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
