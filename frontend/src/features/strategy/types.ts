export const STRATEGY_PANEL_TABS = ["emotion", "prompt", "logs", "memory", "test"] as const;

export type StrategyPanelTab = (typeof STRATEGY_PANEL_TABS)[number];

export function parseStrategyPanelTab(value: string | null): StrategyPanelTab | null {
  if (!value) {
    return null;
  }
  return STRATEGY_PANEL_TABS.includes(value as StrategyPanelTab) ? (value as StrategyPanelTab) : null;
}

export const STRATEGY_TAB_LABELS: Record<StrategyPanelTab, string> = {
  emotion: "情绪",
  prompt: "Prompt",
  logs: "日志",
  memory: "记忆",
  test: "测试",
};
