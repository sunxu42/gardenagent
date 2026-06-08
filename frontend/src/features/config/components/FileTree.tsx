import { ChevronRight, FileCode2, Folder } from "lucide-react";
import type { TreeNode } from "@/services/promptEditorApi";
import { cn } from "@/lib/utils";

interface FileTreeProps {
  nodes: TreeNode[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
  depth?: number;
}

export function FileTree({ nodes, selectedPath, onSelect, depth = 0 }: FileTreeProps) {
  return (
    <ul className="m-0 list-none p-0" role="tree">
      {nodes.map((node) => {
        if (node.type === "dir") {
          return (
            <li key={node.path} role="none">
              <div
                className="flex items-center gap-1.5 truncate py-1.5 text-xs font-medium text-muted-foreground"
                style={{ paddingLeft: depth * 14 + 4 }}
              >
                <Folder className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden />
                <span>{node.name}</span>
              </div>
              {node.children && node.children.length > 0 ? (
                <FileTree
                  nodes={node.children}
                  selectedPath={selectedPath}
                  onSelect={onSelect}
                  depth={depth + 1}
                />
              ) : null}
            </li>
          );
        }
        const selected = selectedPath === node.path;
        const isSoul = node.path.replace(/\\/g, "/") === "soul.yaml";
        return (
          <li key={node.path} role="none">
            <button
              type="button"
              role="treeitem"
              aria-selected={selected}
              className={cn(
                "flex w-full cursor-pointer items-center gap-2 truncate rounded-md py-2 pr-2 text-left text-sm transition-colors",
                "hover:bg-background/80",
                selected && "bg-white font-medium text-foreground shadow-sm"
              )}
              style={{ paddingLeft: depth * 14 + 4 }}
              onClick={() => onSelect(node.path)}
            >
              <FileCode2
                className={cn("h-4 w-4 shrink-0", isSoul ? "text-amber-700" : "text-muted-foreground")}
                aria-hidden
              />
              <span className="min-w-0 flex-1 truncate">{node.name}</span>
              {node.readonly ? (
                <span className="shrink-0 text-[10px] uppercase tracking-wide text-muted-foreground">只读</span>
              ) : null}
              {selected ? <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden /> : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
