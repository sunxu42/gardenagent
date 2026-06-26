import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { StrategyPanel, type StrategyPanelProps } from "@/features/strategy/StrategyPanel";

import "./mobile-strategy.css";

interface MobileStrategySheetProps extends StrategyPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MobileStrategySheet({
  open,
  onOpenChange,
  ...panelProps
}: MobileStrategySheetProps): JSX.Element {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="mobile-strategy-sheet" aria-label="开发者工具">
        <SheetTitle className="sr-only">开发者工具</SheetTitle>
        <StrategyPanel {...panelProps} />
      </SheetContent>
    </Sheet>
  );
}
