import { RailTab, RailTabList } from "@/components/rail/RailTabGroup";
import type { DomainMode } from "@/features/test/types";

const MODES: Array<{ id: DomainMode; label: string }> = [
  { id: "smoke", label: "smoke" },
  { id: "judge", label: "judge" },
  { id: "exploratory", label: "探索" },
];

interface EvalDomainModeTabsProps {
  mode: DomainMode;
  showExploratory: boolean;
  onChange: (mode: DomainMode) => void;
}

export function EvalDomainModeTabs({
  mode,
  showExploratory,
  onChange,
}: EvalDomainModeTabsProps): JSX.Element {
  const items = showExploratory ? MODES : MODES.filter((item) => item.id !== "exploratory");

  return (
    <RailTabList aria-label="域测试模式">
      {items.map((item) => (
        <RailTab key={item.id} selected={mode === item.id} onClick={() => onChange(item.id)}>
          {item.label}
        </RailTab>
      ))}
    </RailTabList>
  );
}
