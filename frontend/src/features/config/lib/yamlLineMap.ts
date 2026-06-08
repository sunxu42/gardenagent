export type YamlLineRange = {
  /** 0-based inclusive */
  startLine: number;
  endLine: number;
};

export type YamlLineIndex = {
  pathRanges: Map<string, YamlLineRange>;
  rootRanges: Map<string, YamlLineRange>;
};

type Anchor = {
  path: string;
  line: number;
  indent: number;
  rootKey: string;
};

function extendBlockEnd(lines: string[], startLine: number, indent: number, initialEnd: number): number {
  let end = initialEnd;
  for (let i = startLine + 1; i <= end; i += 1) {
    const line = lines[i];
    if (line.trim() === "") {
      continue;
    }
    const nextIndent = line.match(/^(\s*)/)?.[1].length ?? 0;
    if (nextIndent <= indent && !line.match(/^\s*-/)) {
      end = i - 1;
      break;
    }
  }
  return Math.max(startLine, end);
}

function collectAnchors(lines: string[]): Anchor[] {
  const anchors: Anchor[] = [];
  const stack: { key: string; indent: number }[] = [];
  const listIndexByParent = new Map<string, number>();

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const listMatch = line.match(/^(\s*)-\s*(.*)$/);
    if (listMatch) {
      const indent = listMatch[1].length;
      const rest = listMatch[2].trim();

      while (stack.length > 0 && stack[stack.length - 1].indent > indent) {
        stack.pop();
      }

      const parentPath = stack.map((s) => s.key).join(".");
      const itemIndex = listIndexByParent.get(parentPath) ?? 0;
      listIndexByParent.set(parentPath, itemIndex + 1);
      const itemPath = parentPath ? `${parentPath}.${itemIndex}` : String(itemIndex);
      const rootKey = stack[0]?.key ?? itemPath.split(".")[0];

      if (rest && /^[\w_-]+:\s*/.test(rest)) {
        const inline = rest.match(/^([\w_-]+):\s*(.*)$/);
        if (inline) {
          const fieldKey = inline[1];
          stack.push({ key: String(itemIndex), indent });
          stack.push({ key: fieldKey, indent: indent + 2 });
          anchors.push({
            path: `${itemPath}.${fieldKey}`,
            line: i,
            indent: indent + 2,
            rootKey,
          });
        }
      } else {
        stack.push({ key: String(itemIndex), indent });
        anchors.push({ path: itemPath, line: i, indent, rootKey });
      }
      continue;
    }

    const keyMatch = line.match(/^(\s*)([\w_-]+):\s*(.*)$/);
    if (!keyMatch) {
      continue;
    }

    const indent = keyMatch[1].length;
    const key = keyMatch[2];

    while (stack.length > 0 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    stack.push({ key, indent });
    listIndexByParent.delete(stack.map((s) => s.key).join("."));

    const path = stack.map((s) => s.key).join(".");
    anchors.push({
      path,
      line: i,
      indent,
      rootKey: stack[0].key,
    });
  }

  return anchors;
}

export function buildYamlLineIndex(content: string): YamlLineIndex {
  const lines = content.split("\n");
  const anchors = collectAnchors(lines);
  const pathRanges = new Map<string, YamlLineRange>();
  const rootRanges = new Map<string, YamlLineRange>();

  const isDescendantPath = (parentPath: string, childPath: string) =>
    childPath === parentPath || childPath.startsWith(`${parentPath}.`);

  for (let a = 0; a < anchors.length; a += 1) {
    const anchor = anchors[a];
    let end = lines.length - 1;
    for (let b = a + 1; b < anchors.length; b += 1) {
      const next = anchors[b];
      if (next.indent < anchor.indent) {
        end = next.line - 1;
        break;
      }
      if (next.indent === anchor.indent && !isDescendantPath(anchor.path, next.path)) {
        end = next.line - 1;
        break;
      }
    }
    end = extendBlockEnd(lines, anchor.line, anchor.indent, end);
    pathRanges.set(anchor.path, { startLine: anchor.line, endLine: end });
  }

  for (const anchor of anchors) {
    if (anchor.indent !== 0) {
      continue;
    }
    const range = pathRanges.get(anchor.path);
    if (range) {
      rootRanges.set(anchor.rootKey, range);
    }
  }

  return { pathRanges, rootRanges };
}

/** Resolve path to line range; walks up prefixes (system.identity → system). */
export function resolvePathRange(index: YamlLineIndex, path: string): YamlLineRange | null {
  const parts = path.split(".").filter(Boolean);
  while (parts.length > 0) {
    const candidate = parts.join(".");
    const hit = index.pathRanges.get(candidate);
    if (hit) {
      return hit;
    }
    parts.pop();
  }
  return null;
}

export function rootKeyFromPath(path: string): string {
  return path.split(".")[0] ?? path;
}

export function scrollCenterLine(range: YamlLineRange): number {
  return range.startLine + Math.floor((range.endLine - range.startLine) / 2);
}
