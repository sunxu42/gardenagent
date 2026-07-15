import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";
const DATA_TABLE_SURFACE_ID = "data-table";
const DATA_TABLE_SELECT_SURFACE_ID = "data-table-select";

interface TableColumn {
  key: string;
  header: string;
}

export type TableRow = {
  id?: string;
  [key: string]: string | undefined;
};

export function renderDataTable(params: {
  title: string;
  columns: TableColumn[];
  rows: TableRow[];
  interactive?: boolean;
  footnote?: string;
  surface_id?: string;
}): A2UIMessage[] {
  const interactive = params.interactive ?? false;
  const surfaceId =
    params.surface_id ?? (interactive ? DATA_TABLE_SELECT_SURFACE_ID : DATA_TABLE_SURFACE_ID);
  const columns = params.columns
    .map((column) => ({
      key: column.key.trim(),
      header: column.header.trim(),
    }))
    .filter((column) => column.key && column.header);
  const rows: Array<Record<string, string> & { id: string }> = params.rows.map((row, index) => ({
    id: (row.id || `row-${index + 1}`).trim(),
    ...Object.fromEntries(
      columns.map((column) => [column.key, String(row[column.key] ?? "").trim()]),
    ),
  }));

  const columnKeys = columns.map((column) => column.key);
  const rootChildren: string[] = ["title"];
  const components: Record<string, unknown>[] = [
    { id: "root", component: "Card", children: rootChildren },
    { id: "title", component: "Text", text: params.title, variant: "h3" },
  ];

  if (interactive) {
    rootChildren.push("table-shell");
    const rowChildren: string[] = [];
    components.push({
      id: "table-shell",
      component: "Column",
      children: ["col-header", "row-list"],
      gap: "sm",
    });
    components.push({
      id: "col-header",
      component: "DataTableColumnHeader",
      columns,
    });
    components.push({ id: "row-list", component: "Column", children: rowChildren });
    rows.forEach((row) => {
      const nodeId = `row-${row.id}`;
      rowChildren.push(nodeId);
      const cells = Object.fromEntries(columnKeys.map((key) => [key, row[key] ?? ""]));
      components.push({
        id: nodeId,
        component: "DataTableRowOption",
        rowId: row.id,
        columnKeys,
        columns,
        cells,
        action: {
          event: {
            name: "confirm_row",
            context: { rowId: row.id, cells },
          },
        },
      });
    });
  } else {
    rootChildren.push("table");
    components.push({
      id: "table",
      component: "DataTable",
      columns,
      data: rows.map((row) => Object.fromEntries(columnKeys.map((key) => [key, row[key] ?? ""]))),
    });
  }

  const footnote = params.footnote?.trim();
  if (footnote) {
    rootChildren.push("footnote");
    components.push({
      id: "footnote",
      component: "Text",
      text: footnote,
      variant: "caption",
      tone: "muted",
    });
  }

  const messages = [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
  ] as A2UIMessage[];

  if (interactive) {
    messages.push({
      version: A2UI_VERSION,
      updateDataModel: { surfaceId, path: "/selectedRow", value: null },
    });
  }

  return messages;
}
