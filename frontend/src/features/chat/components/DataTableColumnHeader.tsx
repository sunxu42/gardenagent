import type { ComponentAdapterProps } from "a2ui-shadcn";

interface TableColumnDef {
  key: string;
  header: string;
}

function readColumns(component: ComponentAdapterProps["component"]): TableColumnDef[] {
  const raw = component.columns;
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }
      const record = item as Record<string, unknown>;
      const key = String(record.key ?? "").trim();
      const header = String(record.header ?? key).trim();
      if (!key) {
        return null;
      }
      return { key, header };
    })
    .filter((item): item is TableColumnDef => item !== null);
}

export function DataTableColumnHeader({ component }: ComponentAdapterProps) {
  const columns = readColumns(component);
  if (columns.length === 0) {
    return null;
  }

  return (
    <div
      className="a2ui-table-header grid gap-2 rounded-t-xl bg-[var(--a2ui-secondary-fill)] px-3 py-2.5"
      style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr)) auto` }}
      role="row"
    >
      {columns.map((column) => (
        <span
          key={column.key}
          className="text-[0.75rem] font-semibold uppercase tracking-wide text-[var(--a2ui-caption)]"
          role="columnheader"
        >
          {column.header}
        </span>
      ))}
      <span className="w-5 shrink-0" aria-hidden />
    </div>
  );
}
