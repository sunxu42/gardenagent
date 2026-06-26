import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Brain, RefreshCw } from "lucide-react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";
import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import { RailPanelBody, RailPanelColumn } from "@/components/rail/RailPanelShell";
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
    <PanelEmpty
      variant="hero"
      icon={Brain}
      title={notFound ? "暂无记忆导出" : "加载失败"}
      description={
        notFound
          ? "memory.yaml 尚未生成。与 Agent 对话产生记忆后，点击「从 Mem0 刷新」即可查看导出内容。"
          : error
      }
      actions={
        notFound ? (
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
        )
      }
    />
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
    <RailPanelColumn className="memory-panel" aria-label="记忆导出">
      <RailPanelHeader
        icon={Brain}
        title="记忆"
        actions={
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
        }
      />

      <RailPanelBody className="memory-panel__body">
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
      </RailPanelBody>
    </RailPanelColumn>
  );
}
