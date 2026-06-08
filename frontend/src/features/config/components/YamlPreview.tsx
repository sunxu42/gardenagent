import { useEffect, useMemo, useRef } from "react";
import type { CSSProperties } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  buildYamlLineIndex,
  resolvePathRange,
  rootKeyFromPath,
  scrollCenterLine,
  type YamlLineIndex,
} from "../lib/yamlLineMap";
import { PanelSection } from "./PanelSection";

interface YamlPreviewProps {
  content: string;
  path: string | null;
  focusedNodePath: string | null;
  flashToken: number;
}

const highlighterStyle: CSSProperties = {
  margin: 0,
  padding: "0.875rem 1rem",
  background: "transparent",
  fontSize: "11px",
  lineHeight: 1.55,
};

function useLineIndex(content: string): YamlLineIndex {
  return useMemo(() => buildYamlLineIndex(content), [content]);
}

export function YamlPreview({ content, path, focusedNodePath, flashToken }: YamlPreviewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const lineIndex = useLineIndex(content);

  const focusRange = focusedNodePath ? resolvePathRange(lineIndex, focusedNodePath) : null;
  const rootKey = focusedNodePath ? rootKeyFromPath(focusedNodePath) : null;
  const rootRange = rootKey ? lineIndex.rootRanges.get(rootKey) : null;

  useEffect(() => {
    if (!focusRange || !scrollRef.current) {
      return;
    }

    const centerLine = scrollCenterLine(focusRange);

    const scrollToLine = () => {
      const container = scrollRef.current;
      if (!container) {
        return;
      }
      const spans = container.querySelectorAll<HTMLElement>("code > span");
      const target = spans[centerLine] ?? spans[focusRange.startLine];
      if (target) {
        target.scrollIntoView({ block: "center", behavior: "smooth" });
        return;
      }
      const lineHeight = 17;
      const offset = centerLine * lineHeight - container.clientHeight / 2;
      container.scrollTo({ top: Math.max(0, offset), behavior: "smooth" });
    };

    const t = window.setTimeout(scrollToLine, 50);
    return () => window.clearTimeout(t);
  }, [focusRange, flashToken, focusedNodePath]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container || !rootRange || flashToken === 0) {
      return;
    }

    const spans = container.querySelectorAll<HTMLElement>("code > span");
    const touched: HTMLElement[] = [];
    for (let i = rootRange.startLine; i <= rootRange.endLine; i += 1) {
      const el = spans[i];
      if (el) {
        el.classList.remove("config-yaml-root-flash-active");
        void el.offsetWidth;
        el.classList.add("config-yaml-root-flash-active");
        touched.push(el);
      }
    }

    const clear = window.setTimeout(() => {
      for (const el of touched) {
        el.classList.remove("config-yaml-root-flash-active");
      }
    }, 1200);

    return () => window.clearTimeout(clear);
  }, [flashToken, rootRange]);

  const lineProps = (lineNumber: number) => {
    const lineIdx = lineNumber - 1;
    const style: CSSProperties = {
      display: "block",
      width: "100%",
      boxSizing: "border-box",
      borderRadius: "2px",
    };

    if (focusRange && lineIdx >= focusRange.startLine && lineIdx <= focusRange.endLine) {
      style.backgroundColor = "hsl(38 62% 46% / 0.12)";
      style.boxShadow = "inset 3px 0 0 hsl(28 62% 46% / 0.75)";
    }

    return { style };
  };

  if (!path) {
    return (
      <PanelSection title="YAML 预览" description="选择文件后查看磁盘原文（只读）" fill>
        <div className="flex min-h-[10rem] flex-1 items-center justify-center rounded-md bg-amber-50/60 px-4">
          <p className="m-0 text-center text-sm text-muted-foreground">在左侧选择 YAML 文件</p>
        </div>
      </PanelSection>
    );
  }

  const lineCount = content ? content.split("\n").length : 0;

  return (
    <PanelSection
      title="YAML 预览"
      description={focusedNodePath ? `联动：${focusedNodePath}` : "聚焦右侧字段可定位到此"}
      fill
      bodyClassName="flex min-h-0 flex-1 flex-col !pb-3"
    >
      <div className="mb-2 flex shrink-0 items-center justify-between gap-2 px-0.5">
        <span className="truncate font-mono text-xs text-muted-foreground">{path}</span>
        <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">{lineCount} 行</span>
      </div>
      <div
        ref={scrollRef}
        className="config-yaml-highlight flex min-h-0 flex-1 overflow-auto rounded-md bg-white/70"
      >
        <SyntaxHighlighter
          language="yaml"
          style={oneLight}
          customStyle={highlighterStyle}
          codeTagProps={{
            style: {
              fontFamily: '"JetBrains Mono", "Cascadia Code", ui-monospace, monospace',
            },
          }}
          showLineNumbers
          wrapLines
          lineProps={lineProps}
          lineNumberStyle={{
            minWidth: "2.25em",
            paddingRight: "1em",
            color: "#94a3b8",
            userSelect: "none",
          }}
        >
          {content || "(空文件)"}
        </SyntaxHighlighter>
      </div>
    </PanelSection>
  );
}
