import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Brain, RefreshCw } from "lucide-react";

import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailToolbarButton } from "@/components/rail/RailToolbarButton";
import {
  fetchPromptContent,
  refreshMemoryYaml,
} from "@/services/promptEditorApi";

import "./memory-panel.css";

const MEMORY_YAML_PATH = "memory/memory.yaml";

function isMemoryNotFound(message: string): boolean {
  return /\b404\b/.test(message);
}

interface MemoryPanelEmptyStateProps {
  error: string;
  refreshing: boolean;
  onRetry: () => void;
  onRefresh: () => void;
}

function MemoryPanelEmptyState({
  error,
  refreshing,
  onRetry,
  onRefresh,
}: MemoryPanelEmptyStateProps): JSX.Element {
  const notFound = isMemoryNotFound(error);

  return (
    <div className="memory-panel__empty">
      <div className="memory-panel__empty-icon" aria-hidden>
        <Brain className="h-8 w-8" strokeWidth={1.5} />
      </div>
      <h3 className="memory-panel__empty-title">
        {notFound ? "暂无记忆导出" : "加载失败"}
      </h3>
      <p className="memory-panel__empty-desc">
        {notFound
          ? "memory.yaml 尚未生成。与 Agent 对话产生记忆后，点击「从 Mem0 刷新」即可查看导出内容。"
          : error}
      </p>
      <div className="memory-panel__empty-actions">
        {notFound ? (
          <RailToolbarButton
            disabled={refreshing}
            icon={
              <RefreshCw
                className={`h-3 w-3${refreshing ? " animate-spin motion-reduce:animate-none" : ""}`}
              />
            }
            onClick={onRefresh}
          >
            {refreshing ? "刷新中…" : "从 Mem0 刷新"}
          </RailToolbarButton>
        ) : (
          <RailToolbarButton onClick={onRetry}>重试</RailToolbarButton>
        )}
      </div>
    </div>
  );
}

const YamlPreview = lazy(() =>
  import("@/features/config/components/YamlPreview").then((module) => ({
    default: module.YamlPreview,
  })),
);

export function MemoryPanel(): JSX.Element {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadedOnce, setLoadedOnce] = useState(false);

  const loadContent = useCallback(async (options?: { silent?: boolean }): Promise<void> => {
    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const result = await fetchPromptContent(MEMORY_YAML_PATH);
      setContent(result.content);
      setLoadedOnce(true);
    } catch (loadError: unknown) {
      setError(loadError instanceof Error ? loadError.message : "无法加载 memory.yaml");
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadContent();
  }, [loadContent]);

  const handleRefresh = async (): Promise<void> => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshMemoryYaml();
      await loadContent({ silent: true });
    } catch (refreshError: unknown) {
      setError(refreshError instanceof Error ? refreshError.message : "刷新记忆失败");
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <section className="memory-panel" aria-label="记忆导出">
      <header className="memory-panel__toolbar">
        <div className="memory-panel__title-row">
          <span className="memory-panel__icon" aria-hidden>
            <Brain className="h-3.5 w-3.5" />
          </span>
          <div className="min-w-0">
            <h2 className="memory-panel__title">记忆</h2>
            <p className="memory-panel__subtitle">Mem0 导出 · 只读</p>
          </div>
        </div>
        <div className="memory-panel__actions">
          <RailToolbarButton
            disabled={refreshing}
            icon={
              <RefreshCw
                className={`h-3 w-3${refreshing ? " animate-spin motion-reduce:animate-none" : ""}`}
              />
            }
            onClick={() => void handleRefresh()}
          >
            {refreshing ? "刷新中…" : "从 Mem0 刷新"}
          </RailToolbarButton>
        </div>
      </header>

      <div className="memory-panel__body">
        {loading && !loadedOnce ? (
          <PanelLoading label="加载记忆文件…" />
        ) : null}

        {!loading && error ? (
          <MemoryPanelEmptyState
            error={error}
            refreshing={refreshing}
            onRetry={() => void loadContent()}
            onRefresh={() => void handleRefresh()}
          />
        ) : null}

        {!error && loadedOnce ? (
          <Suspense fallback={<PanelLoading label="加载预览…" />}>
            <YamlPreview
              content={content}
              path={MEMORY_YAML_PATH}
              focusedNodePath={null}
              flashToken={0}
            />
          </Suspense>
        ) : null}
      </div>
    </section>
  );
}
