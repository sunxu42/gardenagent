import { useCallback, useEffect, useRef, useState } from "react";
import {
  Braces,
  Check,
  ChevronDown,
  ChevronRight,
  List,
  Pencil,
  Plus,
  Trash2,
  Type,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  addChildToMap,
  addRootField,
  insertRootSiblingAfter,
  insertRootSiblingBefore,
  isReadonlyNode,
  removeNodeFromTree,
  renameNodeKey,
  type SoulTreeNode,
  updateNodeInTree,
} from "../lib/soulYamlTree";
import { PanelSection } from "./PanelSection";

interface SoulTreeEditorProps {
  roots: SoulTreeNode[];
  editable: boolean;
  focusedNodePath: string | null;
  onChange: (roots: SoulTreeNode[]) => void;
  onNodeFocus: (path: string) => void;
}

type PendingFocus = { nodeId: string; target: "key" | "value" };

function NodeTypeIcon({ nodeType }: { nodeType: SoulTreeNode["nodeType"] }) {
  if (nodeType === "map") {
    return <Braces className="h-3.5 w-3.5 shrink-0 text-amber-700/85" aria-hidden />;
  }
  if (nodeType === "list" || nodeType === "objectList") {
    return <List className="h-3.5 w-3.5 shrink-0 text-orange-700/75" aria-hidden />;
  }
  return <Type className="h-3.5 w-3.5 shrink-0 text-amber-800/80" aria-hidden />;
}

function typeLabel(nodeType: SoulTreeNode["nodeType"]): string {
  if (nodeType === "map") return "对象";
  if (nodeType === "objectList") return "对象列表";
  if (nodeType === "list") return "字符串列表";
  return "字符串";
}

interface TreeRowProps {
  node: SoulTreeNode;
  depth: number;
  expanded: Set<string>;
  valueOpen: Set<string>;
  editingKeyId: string | null;
  editKeyDraft: string;
  focusedNodePath: string | null;
  onToggleExpand: (id: string) => void;
  onToggleValue: (id: string) => void;
  onStartEditKey: (node: SoulTreeNode) => void;
  onEditKeyDraftChange: (draft: string) => void;
  onSaveEditKey: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
  onInsertBefore: (nodeId: string) => void;
  onInsertAfter: (nodeId: string) => void;
  onAddChild: (mapId: string) => void;
  onChange: (roots: SoulTreeNode[]) => void;
  onNodeFocus: (path: string) => void;
  roots: SoulTreeNode[];
  editable: boolean;
  keyInputRef: React.MutableRefObject<HTMLInputElement | null>;
  valueInputRef: React.MutableRefObject<HTMLTextAreaElement | null>;
  pendingFocus: PendingFocus | null;
  onPendingFocusHandled: () => void;
}

function TreeRow({
  node,
  depth,
  expanded,
  valueOpen,
  editingKeyId,
  editKeyDraft,
  focusedNodePath,
  onToggleExpand,
  onToggleValue,
  onStartEditKey,
  onEditKeyDraftChange,
  onSaveEditKey,
  onDelete,
  onInsertBefore,
  onInsertAfter,
  onAddChild,
  onChange,
  onNodeFocus,
  roots,
  editable,
  keyInputRef,
  valueInputRef,
  pendingFocus,
  onPendingFocusHandled,
}: TreeRowProps) {
  const readonly = isReadonlyNode(node) || !editable;
  const isBranch = node.nodeType === "map" || node.nodeType === "objectList";
  const isOpen = expanded.has(node.id);
  const isValueOpen = valueOpen.has(node.id);
  const isEditingKey = editingKeyId === node.id;
  const indent = depth * 14;
  const canEditKey = depth <= 2 && !readonly;
  const canDelete = depth <= 2 && !readonly;
  const canAddChild = depth <= 1 && node.nodeType === "map" && !readonly;
  const showRootInsertActions = depth === 0 && !readonly;

  const patchRoots = (next: SoulTreeNode[]) => onChange(next);
  const nodePath = node.id;
  const isFocused = focusedNodePath === nodePath;

  const handleFocusNode = () => onNodeFocus(nodePath);

  useEffect(() => {
    if (!pendingFocus || pendingFocus.nodeId !== node.id) {
      return;
    }
    if (pendingFocus.target === "key" && isEditingKey && keyInputRef.current) {
      keyInputRef.current.focus();
      keyInputRef.current.select();
      onPendingFocusHandled();
    }
    if (pendingFocus.target === "value" && isValueOpen && valueInputRef.current) {
      valueInputRef.current.focus();
      onPendingFocusHandled();
    }
  }, [
    pendingFocus,
    node.id,
    isEditingKey,
    isValueOpen,
    keyInputRef,
    valueInputRef,
    onPendingFocusHandled,
  ]);

  const handleRowActivate = () => {
    handleFocusNode();
    if (isBranch) {
      onToggleExpand(node.id);
      return;
    }
    onToggleValue(node.id);
  };

  return (
    <div className="config-tree-node" data-depth={depth}>
      <div
        className={`config-tree-row${isFocused ? " config-tree-row--focused" : ""}${isValueOpen && !isBranch ? " config-tree-row--value-open" : ""}`}
        style={{ paddingLeft: indent }}
      >
        {isBranch ? (
          <button
            type="button"
            className="config-tree-toggle cursor-pointer"
            aria-expanded={isOpen}
            onClick={() => {
              handleFocusNode();
              onToggleExpand(node.id);
            }}
          >
            {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <button
            type="button"
            className="config-tree-toggle cursor-pointer"
            aria-expanded={isValueOpen}
            onClick={handleRowActivate}
          >
            {isValueOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        )}

        <NodeTypeIcon nodeType={node.nodeType} />

        {isEditingKey ? (
          <Input
            ref={isEditingKey ? keyInputRef : undefined}
            className="config-tree-key-input h-7 max-w-[12rem] font-mono text-xs"
            value={editKeyDraft}
            onChange={(e) => onEditKeyDraftChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                onSaveEditKey(node.id);
              }
              if (e.key === "Escape") {
                e.preventDefault();
                onSaveEditKey(node.id);
              }
            }}
            onFocus={handleFocusNode}
            aria-label="字段名"
          />
        ) : (
          <button
            type="button"
            className="config-tree-key-btn cursor-pointer font-mono text-xs"
            title={node.path.join(".")}
            onClick={handleRowActivate}
          >
            {node.key}
          </button>
        )}

        {canEditKey ? (
          <div className="config-tree-key-actions">
            {isEditingKey ? (
              <button
                type="button"
                className="config-tree-icon-btn config-tree-icon-btn--save"
                title="保存字段名"
                aria-label="保存字段名"
                onClick={() => onSaveEditKey(node.id)}
              >
                <Check className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                type="button"
                className="config-tree-icon-btn"
                title="修改字段名"
                aria-label="修改字段名"
                onClick={() => onStartEditKey(node)}
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ) : null}

        <span className="config-tree-type">{typeLabel(node.nodeType)}</span>
        {readonly ? <span className="config-tree-readonly">只读</span> : null}

        {showRootInsertActions || canAddChild || canDelete ? (
          <div className="config-tree-row-actions">
            {showRootInsertActions ? (
              <>
                <button
                  type="button"
                  className="config-tree-text-btn"
                  title="前添字段"
                  onClick={() => onInsertBefore(node.id)}
                >
                  前添
                </button>
                <button
                  type="button"
                  className="config-tree-text-btn"
                  title="后加字段"
                  onClick={() => onInsertAfter(node.id)}
                >
                  后加
                </button>
                {canAddChild ? (
                  <button
                    type="button"
                    className="config-tree-text-btn"
                    title="新增子字段"
                    onClick={() => onAddChild(node.id)}
                  >
                    <Plus className="mr-0.5 h-3 w-3" />
                    子字段
                  </button>
                ) : null}
              </>
            ) : null}

            {depth === 1 && canAddChild && !showRootInsertActions ? (
              <button
                type="button"
                className="config-tree-text-btn"
                title="新增子字段"
                onClick={() => onAddChild(node.id)}
              >
                <Plus className="mr-0.5 h-3 w-3" />
                子字段
              </button>
            ) : null}

            {canDelete && !isEditingKey ? (
              <button
                type="button"
                className="config-tree-icon-btn config-tree-icon-btn--danger"
                title="删除字段及子字段"
                aria-label="删除字段"
                onClick={() => onDelete(node.id)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      {!isBranch && isValueOpen ? (
        <div
          className={`config-tree-leaf${isFocused ? " config-tree-leaf--focused" : ""}`}
          style={{ paddingLeft: indent + 28 }}
        >
          {readonly ? (
            <pre className="config-tree-readonly-value">{node.value || ""}</pre>
          ) : (
            <Textarea
              ref={isValueOpen ? valueInputRef : undefined}
              className="min-h-[88px] border-0 bg-amber-50/90 text-xs ring-1 ring-amber-200/70"
              placeholder={node.nodeType === "list" ? "每行一条" : undefined}
              value={node.value ?? ""}
              onFocus={handleFocusNode}
              onChange={(e) => patchRoots(updateNodeInTree(roots, node.id, { value: e.target.value }))}
            />
          )}
        </div>
      ) : null}

      {isBranch && isOpen && node.children && node.children.length > 0 ? (
        <div className="config-tree-children">
          {node.children.map((child) => (
            <TreeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              expanded={expanded}
              valueOpen={valueOpen}
              editingKeyId={editingKeyId}
              editKeyDraft={editKeyDraft}
              focusedNodePath={focusedNodePath}
              onToggleExpand={onToggleExpand}
              onToggleValue={onToggleValue}
              onStartEditKey={onStartEditKey}
              onEditKeyDraftChange={onEditKeyDraftChange}
              onSaveEditKey={onSaveEditKey}
              onDelete={onDelete}
              onInsertBefore={onInsertBefore}
              onInsertAfter={onInsertAfter}
              onAddChild={onAddChild}
              onChange={onChange}
              onNodeFocus={onNodeFocus}
              roots={roots}
              editable={editable}
              keyInputRef={keyInputRef}
              valueInputRef={valueInputRef}
              pendingFocus={pendingFocus}
              onPendingFocusHandled={onPendingFocusHandled}
            />
          ))}
        </div>
      ) : null}

      {isBranch && isOpen && (!node.children || node.children.length === 0) ? (
        <p className="config-tree-empty" style={{ paddingLeft: indent + 28 }}>
          （空对象，可点「子字段」添加）
        </p>
      ) : null}
    </div>
  );
}

export function SoulTreeEditor({
  roots,
  editable,
  focusedNodePath,
  onChange,
  onNodeFocus,
}: SoulTreeEditorProps) {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const [valueOpen, setValueOpen] = useState<Set<string>>(() => new Set());
  const [editingKeyId, setEditingKeyId] = useState<string | null>(null);
  const [editKeyDraft, setEditKeyDraft] = useState("");
  const [pendingFocus, setPendingFocus] = useState<PendingFocus | null>(null);
  const keyInputRef = useRef<HTMLInputElement | null>(null);
  const valueInputRef = useRef<HTMLTextAreaElement | null>(null);

  const applyFocus = useCallback(
    (nodeId: string, target: PendingFocus["target"], expandIds: string[] = []) => {
      setExpanded((prev) => {
        const next = new Set(prev);
        for (const id of expandIds) {
          next.add(id);
        }
        next.add(nodeId);
        return next;
      });
      if (target === "value") {
        setValueOpen((prev) => new Set(prev).add(nodeId));
      }
      setPendingFocus({ nodeId, target });
      onNodeFocus(nodeId);
    },
    [onNodeFocus]
  );

  const onToggleExpand = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const onToggleValue = useCallback((id: string) => {
    setValueOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const onStartEditKey = useCallback((node: SoulTreeNode) => {
    setEditingKeyId(node.id);
    setEditKeyDraft(node.key);
    onNodeFocus(node.id);
  }, [onNodeFocus]);

  const onSaveEditKey = useCallback(
    (nodeId: string) => {
      const trimmed = editKeyDraft.trim();
      if (trimmed) {
        onChange(renameNodeKey(roots, nodeId, trimmed));
      }
      setEditingKeyId(null);
      setEditKeyDraft("");
    },
    [editKeyDraft, onChange, roots]
  );

  const onDelete = useCallback(
    (nodeId: string) => {
      if (!window.confirm("确定删除该字段及其全部子字段？")) {
        return;
      }
      onChange(removeNodeFromTree(roots, nodeId));
      setEditingKeyId((id) => (id === nodeId ? null : id));
      setValueOpen((prev) => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    },
    [onChange, roots]
  );

  const onInsertBefore = useCallback(
    (nodeId: string) => {
      const { roots: next, newNodeId } = insertRootSiblingBefore(roots, nodeId);
      onChange(next);
      applyFocus(newNodeId, "key");
      setEditingKeyId(newNodeId);
      setEditKeyDraft(next.find((n) => n.id === newNodeId)?.key ?? "");
    },
    [applyFocus, onChange, roots]
  );

  const onInsertAfter = useCallback(
    (nodeId: string) => {
      const { roots: next, newNodeId } = insertRootSiblingAfter(roots, nodeId);
      onChange(next);
      applyFocus(newNodeId, "key");
      setEditingKeyId(newNodeId);
      setEditKeyDraft(next.find((n) => n.id === newNodeId)?.key ?? "");
    },
    [applyFocus, onChange, roots]
  );

  const onAddChild = useCallback(
    (mapId: string) => {
      const { roots: next, newNodeId } = addChildToMap(roots, mapId);
      onChange(next);
      applyFocus(newNodeId, "value", [mapId]);
    },
    [applyFocus, onChange, roots]
  );

  const handleAddRoot = useCallback(() => {
    const next = addRootField(roots);
    const newNode = next[next.length - 1];
    onChange(next);
    applyFocus(newNode.id, "key");
    setEditingKeyId(newNode.id);
    setEditKeyDraft(newNode.key);
  }, [applyFocus, onChange, roots]);

  return (
    <>
      <PanelSection
        title="配置结构"
        description={
          editable
            ? "顶层与二级字段可折叠；点击叶子行展开内容。聚焦时中间预览区同步高亮。"
            : "与预览同构（当前文件只读）"
        }
        fill
        bodyClassName="config-desktop-panel__body--scroll config-scroll-hidden !px-3 !pb-3"
      >
        <div className="config-tree-root space-y-0.5 pb-2">
          {roots.map((node) => (
            <TreeRow
              key={node.id}
              node={node}
              depth={0}
              expanded={expanded}
              valueOpen={valueOpen}
              editingKeyId={editingKeyId}
              editKeyDraft={editKeyDraft}
              focusedNodePath={focusedNodePath}
              onToggleExpand={onToggleExpand}
              onToggleValue={onToggleValue}
              onStartEditKey={onStartEditKey}
              onEditKeyDraftChange={setEditKeyDraft}
              onSaveEditKey={onSaveEditKey}
              onDelete={onDelete}
              onInsertBefore={onInsertBefore}
              onInsertAfter={onInsertAfter}
              onAddChild={onAddChild}
              onChange={onChange}
              onNodeFocus={onNodeFocus}
              roots={roots}
              editable={editable}
              keyInputRef={keyInputRef}
              valueInputRef={valueInputRef}
              pendingFocus={pendingFocus}
              onPendingFocusHandled={() => setPendingFocus(null)}
            />
          ))}
        </div>
      </PanelSection>
      <SoulTreeEditorFooter editable={editable} onAddRoot={handleAddRoot} />
    </>
  );
}

export function SoulTreeEditorFooter({
  editable,
  onAddRoot,
}: {
  editable: boolean;
  onAddRoot: () => void;
}) {
  if (!editable) {
    return null;
  }

  return (
    <footer className="config-editor-footer">
      <Button
        type="button"
        className="cursor-pointer gap-2 bg-amber-800 text-amber-50 hover:bg-amber-900"
        onClick={onAddRoot}
      >
        <Plus className="h-4 w-4" />
        新建顶层字段
      </Button>
      <p className="config-editor-footer__hint">
        点击顶层/二级行展开；叶子行再点一次显示内容。顶层和二级可加子字段，三级可改名/删除。
      </p>
    </footer>
  );
}
