import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

interface SelectInput {
  id: string;
  label: string;
  description?: string;
}

export function renderMultiSelect(params: {
  title: string;
  options: SelectInput[];
  confirm_label?: string;
  surface_id?: string;
}): A2UIMessage[] {
  const surfaceId = params.surface_id ?? "multi-select";
  const confirmLabel = params.confirm_label?.trim() || "确认选择";
  const optionChildren: string[] = [];
  const components: Record<string, unknown>[] = [
    { id: "root", component: "Card", children: ["title", "option-list", "confirm-btn"] },
    { id: "title", component: "Text", text: params.title, variant: "h3" },
    { id: "option-list", component: "Column", children: optionChildren },
    {
      id: "confirm-btn",
      component: "MultiSelectConfirmButton",
      text: confirmLabel,
      action: { event: { name: "confirm_selection" } },
    },
  ];

  params.options.forEach((option, index) => {
    const optionId = (option.id || `option-${index + 1}`).trim();
    const label = (option.label || optionId).trim();
    const nodeId = `option-${optionId}`;
    optionChildren.push(nodeId);
    const node: Record<string, unknown> = {
      id: nodeId,
      component: "MultiSelectOption",
      optionId,
      label,
    };
    if (option.description?.trim()) {
      node.description = option.description.trim();
    }
    components.push(node);
  });

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
    { version: A2UI_VERSION, updateDataModel: { surfaceId, path: "/selectedIds", value: [] } },
  ] as A2UIMessage[];
}
