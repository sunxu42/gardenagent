import { useEffect, useState } from "react";
import type { ComponentAdapterProps } from "a2ui-shadcn";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { a2uiApplePressable, a2uiOptionTextWrap } from "./a2uiAppleClasses";

const SELECTED_ROW_PATH = "/selectedRow";

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

function readCells(
  component: ComponentAdapterProps["component"],
  resolveValue: ComponentAdapterProps["resolveValue"],
): Record<string, string> {
  const resolved = resolveValue(component.cells as Record<string, unknown> | undefined, {});
  if (!resolved || typeof resolved !== "object" || Array.isArray(resolved)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(resolved).map(([key, value]) => [key, String(value ?? "")]),
  );
}

export function DataTableRowOption({
  component,
  dataModel,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const rowId = String(resolveValue(component.rowId as string | undefined, ""));
  const columns = readColumns(component);
  const cells = readCells(component, resolveValue);
  const [isSelected, setIsSelected] = useState(false);

  useEffect(() => {
    const syncSelected = () => {
      setIsSelected(dataModel.get(SELECTED_ROW_PATH) === rowId);
    };
    syncSelected();
    return dataModel.subscribe(SELECTED_ROW_PATH, syncSelected);
  }, [dataModel, rowId]);

  const handleSelect = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;

    if (!action?.event || !rowId) {
      return;
    }

    dataModel.set(SELECTED_ROW_PATH, rowId);
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: action.event.context ?? { rowId, cells },
      timestamp: new Date().toISOString(),
    });
  };

  if (!rowId || columns.length === 0) {
    return null;
  }

  return (
    <Button
      type="button"
      variant="ghost"
      onClick={handleSelect}
      aria-pressed={isSelected}
      className={cn(
        "a2ui-table-row group grid h-auto w-full min-w-0 gap-2 rounded-none px-3 py-3 text-left font-normal shadow-none",
        "border-t border-[var(--a2ui-separator)] bg-[var(--a2ui-cell-bg)] hover:bg-[var(--a2ui-cell-hover)]",
        a2uiApplePressable,
        a2uiOptionTextWrap,
        isSelected && "bg-[var(--a2ui-accent-soft)] hover:bg-[var(--a2ui-accent-soft)]",
      )}
      style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr)) auto` }}
    >
      {columns.map((column) => (
        <span
          key={column.key}
          className={cn(
            "min-w-0 text-[0.875rem] leading-snug whitespace-normal break-words [overflow-wrap:anywhere]",
            isSelected ? "text-[var(--a2ui-accent)]" : "text-[var(--a2ui-title)]",
            column.key === columns[0]?.key ? "font-medium" : "text-[var(--a2ui-body)]",
          )}
        >
          {cells[column.key] ?? ""}
        </span>
      ))}
      <span
        className={cn(
          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors duration-200",
          isSelected
            ? "border-[var(--a2ui-accent)] bg-[var(--a2ui-accent)] text-white"
            : "border-[var(--a2ui-separator)] bg-transparent text-transparent",
        )}
        aria-hidden
      >
        <Check className="h-3 w-3" strokeWidth={3} />
      </span>
    </Button>
  );
}
