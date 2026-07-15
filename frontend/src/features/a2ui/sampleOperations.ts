import type { A2UIMessage } from "a2ui-shadcn";
import { A2UI_CATALOG } from "./catalogIndex";
import { renderDataTable, type TableRow } from "./render/dataTable";
import { renderDatePicker } from "./render/datePicker";
import { renderMultiSelect } from "./render/multiSelect";
import { renderSingleSelect, type SingleSelectParams } from "./render/singleSelect";

type MultiSelectParams = {
  title: string;
  options: Array<{ id: string; label: string; description?: string }>;
  confirm_label?: string;
};

type DatePickerParams = {
  title: string;
  description?: string;
  min_date?: string;
  max_date?: string;
  default_date?: string;
  confirm_label?: string;
};

type DataTableParams = {
  title: string;
  columns: Array<{ key: string; header: string }>;
  rows: TableRow[];
  interactive?: boolean;
  footnote?: string;
};

const RENDERERS = {
  single_select: (params: Record<string, unknown>) =>
    renderSingleSelect(params as SingleSelectParams),
  multi_select: (params: Record<string, unknown>) =>
    renderMultiSelect(params as MultiSelectParams),
  date_picker: (params: Record<string, unknown>) =>
    renderDatePicker(params as DatePickerParams),
  data_table: (params: Record<string, unknown>) => renderDataTable(params as DataTableParams),
} as const;

export function buildSampleOperations(templateId: string, variantId: string): A2UIMessage[] {
  const template = A2UI_CATALOG.find((item) => item.id === templateId);
  if (!template) {
    throw new Error(`unknown template: ${templateId}`);
  }
  const variant = template.sample_variants.find((item) => item.id === variantId);
  if (!variant) {
    throw new Error(`unknown variant: ${templateId}/${variantId}`);
  }
  const render = RENDERERS[template.id as keyof typeof RENDERERS];
  return render(variant.params);
}

export function getTemplateSurfaceId(templateId: string): string {
  const template = A2UI_CATALOG.find((item) => item.id === templateId);
  return template?.surface_id ?? templateId;
}

/** Read surfaceId from rendered operations (interactive variants may differ from catalog default). */
export function resolveSurfaceIdFromOperations(operations: A2UIMessage[]): string {
  for (const op of operations) {
    if ("createSurface" in op && op.createSurface?.surfaceId) {
      return op.createSurface.surfaceId;
    }
  }
  return "";
}
