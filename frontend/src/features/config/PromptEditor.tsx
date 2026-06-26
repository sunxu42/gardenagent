import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { FileCode2, Save } from "lucide-react";

import { PanelLoading } from "@/components/panel/PanelLoading";
import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import { RailToolbarButton } from "@/components/rail/RailToolbarButton";
import { FileTree } from "./components/FileTree";
import { PanelSection } from "./components/PanelSection";
import { SoulTreeEditor } from "./components/SoulTreeEditor";
import { useConfigSplitPane } from "./hooks/useConfigSplitPane";
import {
  dumpSoulYaml,
  objectToTree,
  parseSoulYaml,
  soulPathEditable,
  treeToObject,
  type SoulTreeNode,
} from "./lib/soulYamlTree";
import {
  fetchPromptContent,
  fetchPromptTree,
  savePromptContent,
  type TreeNode,
} from "@/services/promptEditorApi";
import "./config-desktop.css";

const YamlPreview = lazy(() =>
  import("./components/YamlPreview").then((module) => ({
    default: module.YamlPreview,
  })),
);

export function PromptEditor() {
  const { containerRef, ratio, dragging, startDrag } = useConfigSplitPane(0.4);
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [treeLoading, setTreeLoading] = useState(true);
  const [treeError, setTreeError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [preview, setPreview] = useState("");
  const [treeRoots, setTreeRoots] = useState<SoulTreeNode[]>([]);
  const [dirty, setDirty] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [focusedNodePath, setFocusedNodePath] = useState<string | null>(null);
  const [yamlFlashToken, setYamlFlashToken] = useState(0);

  const editable = selectedPath !== null && soulPathEditable(selectedPath);

  const handleNodeFocus = useCallback((path: string) => {
    setFocusedNodePath(path);
    setYamlFlashToken((t) => t + 1);
  }, []);

  const loadTree = useCallback(async () => {
    setTreeLoading(true);
    try {
      const children = await fetchPromptTree();
      setTree(children);
      setTreeError(null);
    } catch {
      setTreeError("无法加载文件树。请确认已运行：python src/server.py");
    } finally {
      setTreeLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTree();
  }, [loadTree]);

  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!dirty) {
        return;
      }
      e.preventDefault();
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty]);

  const loadFile = async (path: string) => {
    setStatus(null);
    try {
      const { content } = await fetchPromptContent(path);
      setPreview(content);
      setSelectedPath(path);
      setTreeRoots(objectToTree(parseSoulYaml(content)));
      setFocusedNodePath(null);
      setDirty(false);
    } catch {
      setStatus("加载文件失败");
    }
  };

  const handleSelectPath = (path: string) => {
    if (dirty) {
      const leave = window.confirm("有未保存的修改，确定切换文件？未保存内容将丢失。");
      if (!leave) {
        return;
      }
    }
    void loadFile(path);
  };

  const handleSave = async () => {
    if (!selectedPath || !editable) {
      return;
    }
    setSaving(true);
    setStatus(null);
    try {
      const text = dumpSoulYaml(treeToObject(treeRoots));
      await savePromptContent(selectedPath, text);
      setPreview(text);
      setDirty(false);
      setStatus("已保存");
    } catch {
      setStatus("保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleTreeChange = (next: SoulTreeNode[]) => {
    setTreeRoots(next);
    setDirty(true);
  };

  if (treeError) {
    return (
      <div className="config-desktop-page config-desktop-page--embedded flex items-center justify-center p-8">
        <div className="max-w-md rounded-lg bg-destructive/10 px-6 py-8 text-center">
          <p className="m-0 text-sm text-destructive">{treeError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="config-desktop-page config-desktop-page--embedded">
      <RailPanelHeader
        icon={FileCode2}
        title="提示词"
        actions={
          <>
            {dirty ? <span className="config-desktop-badge config-desktop-badge--dirty">未保存</span> : null}
            {!editable && selectedPath ? (
              <span className="config-desktop-badge config-desktop-badge--readonly">只读</span>
            ) : null}
            {editable ? (
              <RailToolbarButton
                disabled={!dirty || saving}
                icon={<Save className="h-3 w-3" />}
                onClick={() => void handleSave()}
              >
                {saving ? "保存中…" : "保存"}
              </RailToolbarButton>
            ) : null}
            {status ? (
              <span className="shrink-0 text-xs text-muted-foreground" role="status">
                {status}
              </span>
            ) : null}
          </>
        }
      />

      <div className="config-desktop-columns">
        <aside className="config-desktop-panel--sidebar">
          <PanelSection
            title="文件"
            description="data/prompts"
            fill
            bodyClassName="config-desktop-panel__body--scroll"
          >
            {treeLoading ? (
              <PanelLoading label="加载文件树…" fill={false} className="py-6" />
            ) : (
              <FileTree nodes={tree} selectedPath={selectedPath} onSelect={handleSelectPath} />
            )}
          </PanelSection>
        </aside>

        <div ref={containerRef} className="config-desktop-split">
          <section className="config-desktop-split__preview" style={{ width: `${ratio * 100}%` }}>
            {selectedPath ? (
              <Suspense fallback={<PanelLoading label="加载预览…" fill={false} className="h-full" />}>
                <YamlPreview
                  content={preview}
                  path={selectedPath}
                  focusedNodePath={focusedNodePath}
                  flashToken={yamlFlashToken}
                />
              </Suspense>
            ) : (
              <PanelSection title="配置预览" description="选择文件后查看磁盘原文（只读）" fill>
                <div className="flex min-h-[10rem] flex-1 items-center justify-center rounded-md bg-secondary/40 px-4">
                  <p className="m-0 text-center text-sm text-muted-foreground">在左侧选择配置文件</p>
                </div>
              </PanelSection>
            )}
          </section>

          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="调整预览与编辑区域宽度"
            className={`config-desktop-split__handle${dragging ? " config-desktop-split__handle--active" : ""}`}
            onMouseDown={startDrag}
          />

          <aside className="config-desktop-split__editor">
            <SoulTreeEditor
              roots={treeRoots}
              editable={editable}
              focusedNodePath={focusedNodePath}
              onChange={handleTreeChange}
              onNodeFocus={handleNodeFocus}
            />
          </aside>
        </div>
      </div>
    </div>
  );
}
