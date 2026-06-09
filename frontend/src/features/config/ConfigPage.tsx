import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Save } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FileTree } from "./components/FileTree";
import { PanelSection } from "./components/PanelSection";
import { SoulTreeEditor } from "./components/SoulTreeEditor";
import { YamlPreview } from "./components/YamlPreview";
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

export function ConfigPage() {
  const navigate = useNavigate();
  const { containerRef, ratio, dragging, startDrag } = useConfigSplitPane(0.4);
  const [tree, setTree] = useState<TreeNode[]>([]);
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
    try {
      const children = await fetchPromptTree();
      setTree(children);
      setTreeError(null);
    } catch {
      setTreeError("无法加载文件树。请确认已运行：python src/server.py");
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

  const handleBack = () => {
    if (dirty) {
      const action = window.confirm("有未保存的修改。确定离开？（确定=离开，取消=留在本页）");
      if (!action) {
        return;
      }
    }
    navigate("/");
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
      <div className="config-desktop-page flex items-center justify-center p-8">
        <div className="max-w-md rounded-lg bg-destructive/10 px-6 py-8 text-center">
          <p className="m-0 text-sm text-destructive">{treeError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="config-desktop-page">
      <header className="config-desktop-toolbar">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="cursor-pointer shrink-0"
          aria-label="返回聊天"
          onClick={handleBack}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="min-w-0 flex-1">
          <h1 className="config-desktop-toolbar__title">Prompt 配置</h1>
          {selectedPath ? (
            <p className="config-desktop-toolbar__path truncate">{selectedPath}</p>
          ) : (
            <p className="config-desktop-toolbar__path">yard/prompts</p>
          )}
        </div>
        {dirty ? <span className="config-desktop-badge config-desktop-badge--dirty">未保存</span> : null}
        {!editable && selectedPath ? (
          <span className="config-desktop-badge config-desktop-badge--readonly">只读</span>
        ) : null}
        {editable ? (
          <Button
            type="button"
            className="cursor-pointer shrink-0 gap-2 bg-amber-800 text-amber-50 hover:bg-amber-900"
            disabled={!dirty || saving}
            onClick={() => void handleSave()}
          >
            <Save className="h-4 w-4" />
            {saving ? "保存中…" : "保存"}
          </Button>
        ) : null}
        {status ? (
          <span className="shrink-0 text-xs text-muted-foreground" role="status">
            {status}
          </span>
        ) : null}
      </header>

      <div className="config-desktop-columns">
        <aside className="config-desktop-panel--sidebar">
          <PanelSection
            title="文件"
            description="yard/prompts"
            fill
            bodyClassName="config-desktop-panel__body--scroll"
          >
            <FileTree nodes={tree} selectedPath={selectedPath} onSelect={handleSelectPath} />
          </PanelSection>
        </aside>

        <div ref={containerRef} className="config-desktop-split">
          <section className="config-desktop-split__preview" style={{ width: `${ratio * 100}%` }}>
            <YamlPreview
              content={preview}
              path={selectedPath}
              focusedNodePath={focusedNodePath}
              flashToken={yamlFlashToken}
            />
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
