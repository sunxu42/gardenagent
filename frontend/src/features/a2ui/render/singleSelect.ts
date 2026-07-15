import type { A2UIMessage } from "a2ui-shadcn";
import { renderBinaryChoice } from "./binaryChoice";
import { renderEmojiPicker } from "./emojiPicker";
import { renderPlanSelector } from "./planSelector";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

export type SingleSelectOptionInput = {
  id: string;
  label: string;
  description?: string;
  emoji?: string;
};

export type SingleSelectParams = {
  title: string;
  variant: "default" | "binary" | "emoji" | "cards";
  options: SingleSelectOptionInput[];
  description?: string;
};

export function renderSingleSelect(params: SingleSelectParams): A2UIMessage[] {
  const { variant, options, title, description } = params;
  if (variant === "binary") {
    return renderBinaryChoice({
      title,
      description,
      option_a: { id: options[0].id, label: options[0].label },
      option_b: { id: options[1].id, label: options[1].label },
      surface_id: "single-select-binary",
    });
  }
  if (variant === "emoji") {
    return renderEmojiPicker({
      title,
      options: options.map((o) => ({
        id: o.id,
        label: o.label,
        emoji: o.emoji ?? "",
      })),
      surface_id: "single-select-emoji",
    });
  }
  if (variant === "cards") {
    return renderPlanSelector({
      title,
      plans: options.map((o) => ({
        id: o.id,
        label: o.label,
        description: o.description,
      })),
      surface_id: "single-select-cards",
    });
  }
  return renderDefaultSingleSelect({ title, description, options });
}

function renderDefaultSingleSelect(params: {
  title: string;
  description?: string;
  options: SingleSelectOptionInput[];
}): A2UIMessage[] {
  const surfaceId = "single-select";
  const rootChildren = ["title"];
  const optionChildren: string[] = [];
  const components: Record<string, unknown>[] = [
    { id: "root", component: "Card", children: rootChildren },
    { id: "title", component: "Text", text: params.title, variant: "h3" },
  ];

  if (params.description?.trim()) {
    rootChildren.push("desc");
    components.push({
      id: "desc",
      component: "Text",
      text: params.description.trim(),
      variant: "body",
    });
  }

  rootChildren.push("option-list");
  components.push({ id: "option-list", component: "Column", children: optionChildren });

  params.options.forEach((option, index) => {
    const optionId = (option.id || `option-${index + 1}`).trim();
    const label = (option.label || optionId).trim();
    const nodeId = `option-${optionId}`;
    optionChildren.push(nodeId);
    components.push({
      id: nodeId,
      component: "SingleSelectOption",
      optionId,
      label,
      action: {
        event: {
          name: "confirm_option",
          context: { optionId },
        },
      },
    });
  });

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
    {
      version: A2UI_VERSION,
      updateDataModel: { surfaceId, path: "/selectedOption", value: null },
    },
  ] as A2UIMessage[];
}
