import { lazy, Suspense, type ComponentType } from "react";

import { PanelLoading } from "@/components/panel/PanelLoading";
import type { AffectDebugPanelProps } from "@/features/chat/components/AffectDebugPanel";
import type { LogsPanelProps } from "@/features/logs/LogsPanel";
import type { StrategyPanelTab } from "@/features/strategy/types";

const AffectStrategyPanel = lazy(() =>
  import("@/features/chat/components/AffectDebugPanel").then((m) => ({
    default: m.AffectDebugPanel,
  })),
);

const PromptStrategyPanel = lazy(() =>
  import("@/features/config/PromptEditor").then((m) => ({
    default: m.PromptEditor,
  })),
);

const LogsStrategyPanel = lazy(() =>
  import("@/features/logs/LogsPanel").then((m) => ({
    default: m.LogsPanel,
  })),
);

const TestStrategyPanel = lazy(() =>
  import("@/features/test/TestPanel").then((m) => ({
    default: m.TestPanel,
  })),
);

const MemoryStrategyPanel = lazy(() =>
  import("@/features/memory/MemoryPanel").then((m) => ({
    default: m.MemoryPanel,
  })),
);

const A2UIStrategyPanel = lazy(() =>
  import("@/features/a2ui/A2UIPanel").then((m) => ({
    default: m.A2UIPanel,
  })),
);

const PANEL_IMPORTS: Record<StrategyPanelTab, () => Promise<unknown>> = {
  emotion: () => import("@/features/chat/components/AffectDebugPanel"),
  prompt: () => import("@/features/config/PromptEditor"),
  logs: () => import("@/features/logs/LogsPanel"),
  memory: () => import("@/features/memory/MemoryPanel"),
  a2ui: () => import("@/features/a2ui/A2UIPanel"),
  test: () => import("@/features/test/TestPanel"),
};

export function prefetchStrategyPanel(tab: StrategyPanelTab): void {
  void PANEL_IMPORTS[tab]();
}

function withSuspense<P extends object>(Component: ComponentType<P>) {
  return function SuspendedPanel(props: P) {
    return (
      <Suspense fallback={<PanelLoading />}>
        <Component {...props} />
      </Suspense>
    );
  };
}

export const LazyAffectPanel = withSuspense<AffectDebugPanelProps>(AffectStrategyPanel);

export const LazyPromptPanel = withSuspense(function PromptPanel() {
  return <PromptStrategyPanel />;
});

export const LazyLogsPanel = withSuspense<LogsPanelProps>(LogsStrategyPanel);

export const LazyTestPanel = withSuspense(function TestPanel() {
  return <TestStrategyPanel />;
});

export const LazyMemoryPanel = withSuspense(function MemoryPanelSuspended() {
  return <MemoryStrategyPanel />;
});

export const LazyA2UIPanel = withSuspense(function A2UIPanelSuspended() {
  return <A2UIStrategyPanel />;
});
