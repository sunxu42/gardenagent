import type { LucideIcon } from "lucide-react";

interface StrategyPlaceholderPanelProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function StrategyPlaceholderPanel({
  icon: Icon,
  title,
  description,
}: StrategyPlaceholderPanelProps) {
  return (
    <div className="strategy-placeholder">
      <div className="strategy-placeholder__icon" aria-hidden>
        <Icon className="h-8 w-8" strokeWidth={1.5} />
      </div>
      <h3 className="strategy-placeholder__title">{title}</h3>
      <p className="strategy-placeholder__desc">{description}</p>
    </div>
  );
}
