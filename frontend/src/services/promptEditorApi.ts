const API = "/api/prompt-editor";

export type TreeNode = {
  name: string;
  path: string;
  type: "file" | "dir";
  readonly?: boolean;
  children?: TreeNode[];
};

export async function fetchPromptTree(): Promise<TreeNode[]> {
  const res = await fetch(`${API}/prompts-yaml/tree`);
  if (!res.ok) {
    throw new Error(`tree ${res.status}`);
  }
  const data = (await res.json()) as { children?: TreeNode[] };
  return data.children ?? [];
}

export async function fetchPromptContent(
  path: string
): Promise<{ path: string; content: string; readonly: boolean }> {
  const res = await fetch(`${API}/prompts-yaml/content?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    throw new Error(`content ${res.status}`);
  }
  return res.json();
}

export async function savePromptContent(path: string, content: string): Promise<void> {
  const res = await fetch(`${API}/prompts-yaml/content?path=${encodeURIComponent(path)}`, {
    method: "PUT",
    body: content,
  });
  if (!res.ok) {
    throw new Error(`save ${res.status}`);
  }
}
