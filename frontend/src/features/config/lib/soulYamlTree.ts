import yaml from "js-yaml";

export type SoulTreeNodeType = "map" | "scalar" | "list" | "objectList";

export type SoulTreeNode = {
  id: string;
  key: string;
  path: string[];
  nodeType: SoulTreeNodeType;
  value?: string;
  children?: SoulTreeNode[];
  readonly?: boolean;
};

export const SKIP_ROOT_KEYS = new Set<string>();

export function soulPathEditable(relPath: string): boolean {
  return relPath.trim().length > 0;
}

export function isReadonlyNode(node: SoulTreeNode): boolean {
  return node.readonly === true || (node.path.length > 0 && SKIP_ROOT_KEYS.has(node.path[0]));
}

function buildNode(key: string, val: unknown, path: string[]): SoulTreeNode {
  const id = path.join(".");
  const readonly = path.length > 0 && SKIP_ROOT_KEYS.has(path[0]);

  if (val !== null && typeof val === "object" && Array.isArray(val)) {
    if (val.length > 0 && typeof val[0] === "object" && val[0] !== null) {
      return {
        id,
        key,
        path,
        nodeType: "objectList",
        readonly,
        children: val.map((item, index) => {
          const itemObj = item as Record<string, unknown>;
          const label =
            typeof itemObj.id === "string" && itemObj.id.trim()
              ? String(itemObj.id)
              : `item ${index + 1}`;
          const itemPath = [...path, String(index)];
          return {
            id: itemPath.join("."),
            key: label,
            path: itemPath,
            nodeType: "map",
            readonly,
            children: buildMapChildren(itemObj, itemPath, readonly),
          };
        }),
      };
    }
    return {
      id,
      key,
      path,
      nodeType: "list",
      readonly,
      value: val.map((line) => String(line)).join("\n"),
    };
  }

  if (val !== null && typeof val === "object") {
    return {
      id,
      key,
      path,
      nodeType: "map",
      readonly,
      children: buildMapChildren(val as Record<string, unknown>, path, readonly),
    };
  }

  return {
    id,
    key,
    path,
    nodeType: "scalar",
    readonly,
    value: String(val ?? ""),
  };
}

function buildMapChildren(obj: Record<string, unknown>, path: string[], readonly: boolean): SoulTreeNode[] {
  return Object.entries(obj).map(([key, val]) => buildNode(key, val, [...path, key]));
}

/** Mirror full YAML document as a tree. */
export function objectToTree(obj: Record<string, unknown>): SoulTreeNode[] {
  return Object.entries(obj).map(([key, val]) => buildNode(key, val, [key]));
}

function nodeToValue(node: SoulTreeNode): unknown {
  if (node.nodeType === "map") {
    const out: Record<string, unknown> = {};
    for (const child of node.children ?? []) {
      out[child.key] = nodeToValue(child);
    }
    return out;
  }
  if (node.nodeType === "list") {
    return (node.value ?? "")
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  if (node.nodeType === "objectList") {
    return (node.children ?? []).map((child) => nodeToValue(child));
  }
  return node.value ?? "";
}

export function treeToObject(roots: SoulTreeNode[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const root of roots) {
    out[root.key] = nodeToValue(root);
  }
  return out;
}

export function dumpSoulYaml(obj: Record<string, unknown>): string {
  return yaml.dump(obj, { lineWidth: -1, noRefs: true });
}

export function parseSoulYaml(text: string): Record<string, unknown> {
  const loaded = yaml.load(text);
  return loaded && typeof loaded === "object" && !Array.isArray(loaded)
    ? (loaded as Record<string, unknown>)
    : {};
}

export function updateNodeInTree(
  roots: SoulTreeNode[],
  nodeId: string,
  patch: Partial<Pick<SoulTreeNode, "key" | "value">>
): SoulTreeNode[] {
  return roots.map((node) => patchNode(node, nodeId, patch));
}

function patchNode(node: SoulTreeNode, nodeId: string, patch: Partial<Pick<SoulTreeNode, "key" | "value">>): SoulTreeNode {
  if (node.id === nodeId) {
    return { ...node, ...patch };
  }
  if (!node.children) {
    return node;
  }
  return { ...node, children: node.children.map((c) => patchNode(c, nodeId, patch)) };
}

export function removeNodeFromTree(roots: SoulTreeNode[], nodeId: string): SoulTreeNode[] {
  const filtered = roots
    .filter((n) => n.id !== nodeId)
    .map((n) => ({
      ...n,
      children: n.children ? removeNodeFromTree(n.children, nodeId) : undefined,
    }));
  return filtered;
}

export function addRootField(roots: SoulTreeNode[], key = "new_section"): SoulTreeNode[] {
  const path = [key];
  const unique = uniqueKeyAmong(roots.map((n) => n.key), key);
  return [
    ...roots,
    {
      id: unique,
      key: unique,
      path: [unique],
      nodeType: "map",
      children: [],
    },
  ];
}

function uniqueKeyAmong(existing: string[], base: string): string {
  if (!existing.includes(base)) {
    return base;
  }
  let i = 2;
  while (existing.includes(`${base}_${i}`)) {
    i += 1;
  }
  return `${base}_${i}`;
}

function uniqueChildKey(children: SoulTreeNode[], base: string): string {
  return uniqueKeyAmong(children.map((c) => c.key), base);
}

function createScalarChild(parentPath: string[], key: string): SoulTreeNode {
  const path = [...parentPath, key];
  return {
    id: path.join("."),
    key,
    path,
    nodeType: "scalar",
    value: "",
  };
}

/** Rebuild ``id`` / ``path`` for a subtree after a key rename. */
export function rekeyNodeSubtree(node: SoulTreeNode, newKey: string): SoulTreeNode {
  const parentPath = node.path.slice(0, -1);
  const newPath = [...parentPath, newKey];
  const next: SoulTreeNode = {
    ...node,
    key: newKey,
    path: newPath,
    id: newPath.join("."),
  };
  if (next.children) {
    next.children = next.children.map((child) => {
      const childPath = [...newPath, child.key];
      return rekeyNodeSubtree({ ...child, path: childPath, id: childPath.join(".") }, child.key);
    });
  }
  return next;
}

export function renameNodeKey(roots: SoulTreeNode[], nodeId: string, newKey: string): SoulTreeNode[] {
  const trimmed = newKey.trim();
  if (!trimmed) {
    return roots;
  }
  return roots.map((node) => renameNodeKeyNode(node, nodeId, trimmed));
}

function renameNodeKeyNode(node: SoulTreeNode, nodeId: string, newKey: string): SoulTreeNode {
  if (node.id === nodeId) {
    if (node.key === newKey) {
      return node;
    }
    return rekeyNodeSubtree(node, newKey);
  }
  if (!node.children) {
    return node;
  }
  return { ...node, children: node.children.map((c) => renameNodeKeyNode(c, nodeId, newKey)) };
}

export function insertRootSiblingBefore(
  roots: SoulTreeNode[],
  nodeId: string,
  key = "new_section"
): { roots: SoulTreeNode[]; newNodeId: string } {
  const idx = roots.findIndex((n) => n.id === nodeId);
  if (idx < 0) {
    return { roots, newNodeId: "" };
  }
  const unique = uniqueKeyAmong(roots.map((n) => n.key), key);
  const newNode: SoulTreeNode = {
    id: unique,
    key: unique,
    path: [unique],
    nodeType: "map",
    children: [],
  };
  return {
    roots: [...roots.slice(0, idx), newNode, ...roots.slice(idx)],
    newNodeId: newNode.id,
  };
}

export function insertRootSiblingAfter(
  roots: SoulTreeNode[],
  nodeId: string,
  key = "new_section"
): { roots: SoulTreeNode[]; newNodeId: string } {
  const idx = roots.findIndex((n) => n.id === nodeId);
  if (idx < 0) {
    return { roots, newNodeId: "" };
  }
  const unique = uniqueKeyAmong(roots.map((n) => n.key), key);
  const newNode: SoulTreeNode = {
    id: unique,
    key: unique,
    path: [unique],
    nodeType: "map",
    children: [],
  };
  return {
    roots: [...roots.slice(0, idx + 1), newNode, ...roots.slice(idx + 1)],
    newNodeId: newNode.id,
  };
}

export function addChildToMap(
  roots: SoulTreeNode[],
  mapId: string,
  childKey = "new_field"
): { roots: SoulTreeNode[]; newNodeId: string } {
  let newNodeId = "";
  const next = roots.map((node) => {
    const patched = addChildToMapNode(node, mapId, childKey);
    if (patched.newNodeId) {
      newNodeId = patched.newNodeId;
    }
    return patched.node;
  });
  return { roots: next, newNodeId };
}

function addChildToMapNode(
  node: SoulTreeNode,
  mapId: string,
  childKey: string
): { node: SoulTreeNode; newNodeId: string } {
  if (node.id === mapId && node.nodeType === "map" && !isReadonlyNode(node)) {
    const unique = uniqueChildKey(node.children ?? [], childKey);
    const child = createScalarChild(node.path, unique);
    return {
      node: { ...node, children: [...(node.children ?? []), child] },
      newNodeId: child.id,
    };
  }
  if (node.children) {
    let newNodeId = "";
    const children = node.children.map((c) => {
      const patched = addChildToMapNode(c, mapId, childKey);
      if (patched.newNodeId) {
        newNodeId = patched.newNodeId;
      }
      return patched.node;
    });
    return { node: { ...node, children }, newNodeId };
  }
  return { node, newNodeId: "" };
}
