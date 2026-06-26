import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Brain, RefreshCw } from "lucide-react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";
import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailToolbarButton } from "@/components/rail/RailToolbarButton";
import {
  fetchPromptContent,
  refreshMemoryYaml,
} from "@/services/promptEditorApi";

import "./memory-panel.css";

const MEMORY_YAML_PATH = "memory/memory.yaml";

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
          <PanelEmpty
            title="加载失败"
            description={error}
            action={
              <button className="panel-state__action" type="button" onClick={() => void loadContent()}>
                重试
              </button>
            }
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
