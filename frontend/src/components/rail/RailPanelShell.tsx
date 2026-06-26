import { forwardRef, type ComponentPropsWithoutRef, type ElementType } from "react";

import { cn } from "@/lib/utils";

type PolymorphicProps<T extends ElementType> = {
  as?: T;
  className?: string;
} & Omit<ComponentPropsWithoutRef<T>, "as" | "className">;

/** Column shell for a strategy-rail tab (header + body). */
export function RailPanelRoot({
  as: Tag = "section",
  className,
  ...props
}: PolymorphicProps<"section" | "div">): JSX.Element {
  return <Tag className={cn("rail-panel-root", className)} {...props} />;
}

/** Full-height single-column panel (logs, memory). */
export function RailPanelColumn({
  as: Tag = "section",
  className,
  ...props
}: PolymorphicProps<"section" | "div">): JSX.Element {
  return <Tag className={cn("rail-panel-column", className)} {...props} />;
}

/** Scrollable or static content area below a panel header. */
export function RailPanelBody({
  className,
  ...props
}: ComponentPropsWithoutRef<"div">): JSX.Element {
  return <div className={cn("rail-panel-body", className)} {...props} />;
}

/** Horizontal split container (list + detail). */
export function RailSidebarGroup({
  className,
  ...props
}: ComponentPropsWithoutRef<"div">): JSX.Element {
  return <div className={cn("rail-sidebar-group", className)} {...props} />;
}

/** Left / list column in a split layout. */
export function RailListPane({
  as: Tag = "aside",
  className,
  ...props
}: PolymorphicProps<"aside" | "div">): JSX.Element {
  return <Tag className={cn("rail-list-pane", className)} {...props} />;
}

/** Right / detail column in a split layout. */
export function RailDetailPane({
  as: Tag = "aside",
  className,
  ...props
}: PolymorphicProps<"aside" | "div">): JSX.Element {
  return <Tag className={cn("rail-detail-pane", className)} {...props} />;
}

interface RailPanelScrollProps extends ComponentPropsWithoutRef<"div"> {
  padded?: boolean;
}

/** Flex-growing scroll region inside a list or detail pane. */
export const RailPanelScroll = forwardRef<HTMLDivElement, RailPanelScrollProps>(function RailPanelScroll(
  { padded = false, className, ...props },
  ref,
): JSX.Element {
  return (
    <div
      ref={ref}
      className={cn("rail-panel-scroll", padded && "rail-panel-scroll--padded", className)}
      {...props}
    />
  );
});
RailPanelScroll.displayName = "RailPanelScroll";
