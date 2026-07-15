import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { A2UIProviderShell } from "../components/A2UIProviderShell";
import { A2UISurface } from "../components/A2UISurface";
import { showUiActionToast } from "../lib/uiActionToast";
import type { A2uiPart, ChatMessage } from "../types";
import { PLAN_SELECTOR_DEMO_SURFACE_ID, planSelectorDemoMessages } from "./planSelectorDemo";

const demoPart: A2uiPart = {
  type: "a2ui",
  surfaceId: PLAN_SELECTOR_DEMO_SURFACE_ID,
  messages: planSelectorDemoMessages,
  status: "ready",
  interaction: "pending",
};

const demoMessage: ChatMessage = {
  id: "a2ui-demo-message",
  role: "assistant",
  parts: [demoPart],
  content: "",
  status: "done",
  runId: "demo-run",
};

export function A2UIDemoPage() {
  const [readOnly, setReadOnly] = useState(false);

  return (
    <A2UIProviderShell>
      <div className="mx-auto flex min-h-screen max-w-2xl flex-col gap-4 bg-background p-4 text-foreground">
        <header className="rounded-lg border border-border bg-muted/40 px-4 py-3">
          <h1 className="text-lg font-semibold">A2UI Manual Demo</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            静态方案选择卡片，用于验证自定义 PlanOptionCard 渲染与整卡点击交互。
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm">
              <Link to="/">返回聊天</Link>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setReadOnly((value) => !value)}
            >
              {readOnly ? "切换为可交互" : "切换为只读（模拟历史）"}
            </Button>
          </div>
        </header>

        <main className="rounded-xl border border-border bg-muted px-3 py-2.5 shadow-sm">
          <A2UISurface
            part={{
              ...demoPart,
              interaction: readOnly ? "resolved" : "pending",
            }}
            message={{
              ...demoMessage,
              status: readOnly ? "done" : "streaming",
            }}
            connectionOnline={!readOnly}
            onAction={(action) => {
              const planId =
                action.context && typeof action.context.planId === "string"
                  ? action.context.planId
                  : "未知方案";
              showUiActionToast(`Demo：已选择 ${planId}`);
            }}
          />
        </main>
      </div>
    </A2UIProviderShell>
  );
}
