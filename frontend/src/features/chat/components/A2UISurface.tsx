import { Component, type ErrorInfo, type ReactNode } from "react";
import { A2UISurface as A2UIProtocolSurface } from "a2ui-shadcn";
import type { A2UIActionPayload, A2uiPart, ChatMessage } from "../types";
import { isA2uiPartInteractable } from "../lib/a2uiInteractive";
import { a2uiComponentRegistry } from "./a2uiComponentRegistry";
import "./a2ui-apple.css";

interface A2UISurfaceProps {
  part: A2uiPart;
  message: ChatMessage;
  connectionOnline?: boolean;
  onAction: (action: A2UIActionPayload) => void;
}

interface A2UISurfaceErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface A2UISurfaceErrorBoundaryState {
  hasError: boolean;
}

class A2UISurfaceErrorBoundary extends Component<
  A2UISurfaceErrorBoundaryProps,
  A2UISurfaceErrorBoundaryState
> {
  state: A2UISurfaceErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): A2UISurfaceErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("[a2ui] render failed", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export function A2UISurface({
  part,
  message,
  connectionOnline = true,
  onAction,
}: A2UISurfaceProps) {
  const interactionDisabled = !isA2uiPartInteractable(part, message, connectionOnline);
  const showRawDebug = typeof window !== "undefined" && window.location.hostname === "localhost";

  return (
    <div
      className="a2ui-apple-surface a2ui-in-bubble"
      data-disabled={interactionDisabled ? "true" : "false"}
    >
      <div className="a2ui-apple-surface__shell">
        <A2UISurfaceErrorBoundary
          fallback={
            <div className="rounded-xl bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
              界面渲染失败
              {showRawDebug ? (
                <details className="mt-2 text-xs text-muted-foreground">
                  <summary>原始 JSON</summary>
                  <pre className="mt-1 overflow-auto rounded-lg bg-black/5 p-2 dark:bg-white/5">
                    {JSON.stringify(part.messages, null, 2)}
                  </pre>
                </details>
              ) : null}
            </div>
          }
        >
          <A2UIProtocolSurface
            surfaceId={part.surfaceId}
            messages={part.messages}
            componentRegistry={a2uiComponentRegistry}
            className="a2ui-apple-protocol space-y-3"
            onAction={(action) => {
              if (interactionDisabled) {
                return;
              }
              onAction({
                name: action.name,
                context: action.context,
                sourceComponentId: action.sourceComponentId,
                dataModel: action.dataModel,
              });
            }}
          />
        </A2UISurfaceErrorBoundary>
      </div>
    </div>
  );
}
