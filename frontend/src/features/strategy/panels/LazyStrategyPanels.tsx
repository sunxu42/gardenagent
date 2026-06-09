import { lazy, Suspense, type ComponentType } from "react";
import { Brain } from "lucide-react";
import type { AffectDebugPanelProps } from "@/features/chat/components/AffectDebugPanel";
import type { LogsPanelProps } from "@/features/logs/LogsPanel";
import { StrategyPlaceholderPanel } from "./StrategyPlaceholderPanel";

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

function PanelFallback() {
  return (
    <div className="strategy-panel-loading" role="status" aria-live="polite">
      <span className="strategy-panel-loading__spinner" aria-hidden />
      加载中…
    </div>
  );
}

function withSuspense<P extends object>(Component: ComponentType<P>) {
  return function SuspendedPanel(props: P) {
    return (
      <Suspense fallback={<PanelFallback />}>
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

export function MemoryPanel() {
  return (
    <StrategyPlaceholderPanel
      icon={Brain}
      title="记忆"
      description="长期记忆、情景记忆与检索结果将在此浏览与管理。功能开发中。"
    />
  );
}
