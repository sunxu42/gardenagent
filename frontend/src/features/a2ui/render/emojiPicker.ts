import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

interface EmojiInput {
  id: string;
  emoji: string;
  label: string;
}

export function renderEmojiPicker(params: {
  title: string;
  options: EmojiInput[];
  surface_id?: string;
}): A2UIMessage[] {
  const surfaceId = params.surface_id ?? "single-select-emoji";
  const optionChildren: string[] = [];
  const components: Record<string, unknown>[] = [
    { id: "root", component: "Card", children: ["title", "option-list"] },
    { id: "title", component: "Text", text: params.title, variant: "h3" },
    { id: "option-list", component: "Column", children: optionChildren },
  ];

  params.options.forEach((option, index) => {
    const optionId = (option.id || `emoji-${index + 1}`).trim();
    const emoji = option.emoji.trim();
    const label = (option.label || optionId).trim();
    const nodeId = `emoji-${optionId}`;
    optionChildren.push(nodeId);
    components.push({
      id: nodeId,
      component: "EmojiOption",
      optionId,
      emoji,
      label,
      action: {
        event: {
          name: "confirm_emoji",
          context: { optionId, emoji },
        },
      },
    });
  });

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
    { version: A2UI_VERSION, updateDataModel: { surfaceId, path: "/selectedEmoji", value: null } },
  ] as A2UIMessage[];
}
