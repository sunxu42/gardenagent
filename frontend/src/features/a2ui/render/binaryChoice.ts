import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

interface BinaryInput {
  id: string;
  label: string;
}

export function renderBinaryChoice(params: {
  title: string;
  option_a: BinaryInput;
  option_b: BinaryInput;
  description?: string;
  surface_id?: string;
}): A2UIMessage[] {
  const surfaceId = params.surface_id ?? "single-select-binary";
  const rootChildren = ["title"];
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

  rootChildren.push("choices");
  components.push({
    id: "choices",
    component: "Row",
    children: ["choice-a", "choice-b"],
  });

  (
    [
      ["a", params.option_a, "primary"],
      ["b", params.option_b, "secondary"],
    ] as const
  ).forEach(([suffix, option, variant]) => {
    const choiceId = option.id.trim();
    components.push({
      id: `choice-${suffix}`,
      component: "BinaryChoiceButton",
      choiceId,
      label: option.label.trim(),
      variant,
      action: {
        event: {
          name: "confirm_choice",
          context: { choiceId },
        },
      },
    });
  });

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
  ] as A2UIMessage[];
}
