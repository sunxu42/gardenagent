import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface TestPanelCollapsibleSectionProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function TestPanelCollapsibleSection({
  title,
  children,
  defaultOpen = true,
  className,
}: TestPanelCollapsibleSectionProps): JSX.Element {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <section className={cn("test-panel-collapsible", className)}>
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            className="test-panel-collapsible__trigger h-auto w-full justify-between rounded-none px-0 py-0 font-normal shadow-none hover:bg-transparent"
          >
            <span className="test-panel-collapsible__title">{title}</span>
            <ChevronDown
              className={cn(
                "test-panel-collapsible__chevron h-3.5 w-3.5 shrink-0",
                open && "test-panel-collapsible__chevron--open",
              )}
              aria-hidden
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="test-panel-collapsible__body">
          {children}
        </CollapsibleContent>
      </section>
    </Collapsible>
  );
}
