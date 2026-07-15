import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

export function renderDatePicker(params: {
  title: string;
  description?: string;
  min_date?: string;
  max_date?: string;
  default_date?: string;
  confirm_label?: string;
  surface_id?: string;
}): A2UIMessage[] {
  const surfaceId = params.surface_id ?? "date-picker";
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

  rootChildren.push("picker");
  const picker: Record<string, unknown> = {
    id: "picker",
    component: "DatePicker",
    confirmLabel: params.confirm_label?.trim() || "确认日期",
    action: { event: { name: "confirm_date" } },
  };
  if (params.min_date?.trim()) {
    picker.minDate = params.min_date.trim();
  }
  if (params.max_date?.trim()) {
    picker.maxDate = params.max_date.trim();
  }
  if (params.default_date?.trim()) {
    picker.defaultDate = params.default_date.trim();
  }
  components.push(picker);

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
    {
      version: A2UI_VERSION,
      updateDataModel: { surfaceId, path: "/selectedDate", value: null },
    },
  ] as A2UIMessage[];
}
