import type { A2UIMessage } from "a2ui-shadcn";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { A2UISurface } from "@/features/chat/components/A2UISurface";
import type { A2UIActionPayload, A2uiPart, ChatMessage } from "@/features/chat/types";
import { isInteractiveA2uiSurface } from "@/features/chat/lib/a2uiInteractive";
import { A2UIChatBubblePreview } from "./A2UIChatBubblePreview";
import { resolveSurfaceIdFromOperations } from "./sampleOperations";
import type { A2UITemplateCatalogEntry } from "./types";
import "./a2ui-panel.css";

interface A2UITemplatePreviewProps {
  template: A2UITemplateCatalogEntry | undefined;
  variantId: string;
  onVariantChange: (variantId: string) => void;
  operations: A2UIMessage[];
  onAction: (action: A2UIActionPayload) => void;
}

export function A2UITemplatePreview({
  template,
  variantId,
  onVariantChange,
  operations,
  onAction,
}: A2UITemplatePreviewProps) {
  if (!template) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        请选择一个模板
      </div>
    );
  }

  const surfaceId = resolveSurfaceIdFromOperations(operations) || template.surface_id;
  const part: A2uiPart = {
    type: "a2ui",
    surfaceId,
    messages: operations,
    status: "ready",
    interaction: isInteractiveA2uiSurface(surfaceId) ? "pending" : undefined,
  };

  const message: ChatMessage = {
    id: "a2ui-gallery-preview",
    role: "assistant",
    parts: [part],
    content: "",
    status: "streaming",
    runId: "gallery-preview",
  };

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col">
      <div className="a2ui-panel-meta space-y-3">
        <div>
          <h4 className="text-sm font-semibold text-[var(--apple-label)]">{template.name}</h4>
          <p className="mt-1 text-sm leading-relaxed text-[var(--apple-secondary-label)]">
            {template.scenario}
          </p>
        </div>

        <div className="a2ui-panel-meta__card">
          <div className="text-xs font-medium text-[var(--apple-secondary-label)]">示例话术</div>
          <ul className="mt-1 list-inside list-disc text-sm text-[var(--apple-label)]">
            {template.trigger_examples.map((example) => (
              <li key={example}>{example}</li>
            ))}
          </ul>
        </div>

        {template.anti_patterns.length > 0 ? (
          <div className="a2ui-panel-meta__card text-xs text-[var(--apple-secondary-label)]">
            <span className="font-medium text-[var(--apple-label)]">避免：</span>
            {template.anti_patterns.join("；")}
          </div>
        ) : null}

        <ToggleGroup
          type="single"
          value={variantId}
          onValueChange={(next) => {
            if (next) {
              onVariantChange(next);
            }
          }}
          className="a2ui-panel-meta__variants flex flex-wrap justify-start gap-0"
        >
          {template.sample_variants.map((variant) => (
            <ToggleGroupItem
              key={variant.id}
              value={variant.id}
              className={
                variant.id === variantId
                  ? "a2ui-panel-meta__variant a2ui-panel-meta__variant--active h-auto rounded-md border-0 bg-transparent px-0 py-0 shadow-none data-[state=on]:bg-transparent"
                  : "a2ui-panel-meta__variant a2ui-panel-meta__variant--idle h-auto rounded-md border-0 bg-transparent px-0 py-0 shadow-none data-[state=on]:bg-transparent"
              }
            >
              {variant.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <A2UIChatBubblePreview userPreviewText={template.trigger_examples[0]}>
        {operations.length > 0 ? (
          <A2UISurface
            part={part}
            message={message}
            connectionOnline
            onAction={onAction}
          />
        ) : (
          <p className="text-sm text-muted-foreground">无法加载预览</p>
        )}
      </A2UIChatBubblePreview>
    </div>
  );
}
