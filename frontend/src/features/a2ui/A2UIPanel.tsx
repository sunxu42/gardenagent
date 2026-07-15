import { LayoutTemplate } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { RailPanelHeader } from "@/components/rail/RailPanelHeader";
import { A2UIProviderShell } from "@/features/chat/components/A2UIProviderShell";
import { showUiActionToast } from "@/features/chat/lib/uiActionToast";
import type { A2UIActionPayload } from "@/features/chat/types";
import { A2UITemplateList } from "./A2UITemplateList";
import { A2UITemplatePreview } from "./A2UITemplatePreview";
import { A2UI_CATALOG } from "./catalogIndex";
import { buildSampleOperations } from "./sampleOperations";

export function A2UIPanel() {
  const [selectedId, setSelectedId] = useState(A2UI_CATALOG[0]?.id ?? "");
  const [variantId, setVariantId] = useState("");

  const template = useMemo(
    () => A2UI_CATALOG.find((item) => item.id === selectedId),
    [selectedId],
  );

  useEffect(() => {
    setVariantId(template?.sample_variants[0]?.id ?? "");
  }, [template?.id, template?.sample_variants]);

  const operations = useMemo(() => {
    if (!template || !variantId) {
      return [];
    }
    try {
      return buildSampleOperations(template.id, variantId);
    } catch {
      return [];
    }
  }, [template, variantId]);

  const handleAction = useCallback((action: A2UIActionPayload) => {
    const context = action.context ?? {};
    const summary = Object.entries(context)
      .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
      .join(", ");
    showUiActionToast(summary ? `操作 ${action.name}：${summary}` : `操作 ${action.name}`);
  }, []);

  return (
    <A2UIProviderShell>
      <div className="flex h-full min-h-0 flex-col" role="region" aria-label="A2UI 模板画廊">
        <RailPanelHeader
          level={3}
          icon={LayoutTemplate}
          title="A2UI 交互卡片"
          actionPlaceholder
        />
        <div className="flex min-h-0 flex-1 overflow-hidden">
          <A2UITemplateList
            templates={A2UI_CATALOG}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <A2UITemplatePreview
            template={template}
            variantId={variantId}
            onVariantChange={setVariantId}
            operations={operations}
            onAction={handleAction}
          />
        </div>
      </div>
    </A2UIProviderShell>
  );
}
