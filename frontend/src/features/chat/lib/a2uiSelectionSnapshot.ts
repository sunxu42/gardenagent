import type { A2UIMessage } from "a2ui-shadcn";
import type { A2UIActionPayload, A2uiPart } from "../types";

const A2UI_VERSION = "v0.9";

interface SelectionBinding {
  path: string;
  readValue: (context: Record<string, unknown> | undefined) => unknown;
}

const SURFACE_SELECTION_BINDINGS: Record<string, SelectionBinding[]> = {
  "single-select": [
    {
      path: "/selectedOption",
      readValue: (context) => context?.optionId,
    },
  ],
  "single-select-cards": [
    {
      path: "/selectedPlan",
      readValue: (context) => context?.planId,
    },
  ],
  "single-select-emoji": [
    {
      path: "/selectedEmoji",
      readValue: (context) => context?.optionId,
    },
  ],
  "single-select-binary": [
    {
      path: "/selectedChoice",
      readValue: (context) => context?.choiceId,
    },
  ],
  // Legacy surface ids kept for IndexedDB history rehydration.
  "plan-selector": [
    {
      path: "/selectedPlan",
      readValue: (context) => context?.planId,
    },
  ],
  "multi-select": [
    {
      path: "/selectedIds",
      readValue: (context) => context?.selectedIds,
    },
  ],
  "emoji-picker": [
    {
      path: "/selectedEmoji",
      readValue: (context) => context?.optionId,
    },
  ],
  "date-picker": [
    {
      path: "/selectedDate",
      readValue: (context) => context?.date,
    },
  ],
  "data-table-select": [
    {
      path: "/selectedRow",
      readValue: (context) => context?.rowId,
    },
  ],
};

function dataModelUpdateOp(
  surfaceId: string,
  path: string,
  value: unknown,
): A2UIMessage {
  return {
    version: A2UI_VERSION,
    updateDataModel: { surfaceId, path, value },
  } as A2UIMessage;
}

function readDataModelPathEntries(
  dataModel: Record<string, unknown> | undefined,
): Array<{ path: string; value: unknown }> {
  if (!dataModel) {
    return [];
  }
  return Object.entries(dataModel)
    .filter(([path, value]) => path.startsWith("/") && value !== undefined)
    .map(([path, value]) => ({ path, value }));
}

/** Build updateDataModel ops so selection state survives IndexedDB round-trips. */
export function buildSelectionDataModelOps(
  surfaceId: string,
  action: Pick<A2UIActionPayload, "context" | "dataModel">,
): A2UIMessage[] {
  const ops: A2UIMessage[] = [];
  const seenPaths = new Set<string>();

  for (const binding of SURFACE_SELECTION_BINDINGS[surfaceId] ?? []) {
    const value = binding.readValue(action.context);
    if (value === undefined) {
      continue;
    }
    ops.push(dataModelUpdateOp(surfaceId, binding.path, value));
    seenPaths.add(binding.path);
  }

  for (const { path, value } of readDataModelPathEntries(action.dataModel)) {
    if (seenPaths.has(path)) {
      continue;
    }
    ops.push(dataModelUpdateOp(surfaceId, path, value));
    seenPaths.add(path);
  }

  return ops;
}

export function appendSelectionSnapshot(
  part: A2uiPart,
  action: Pick<A2UIActionPayload, "context" | "dataModel">,
): A2uiPart {
  const ops = buildSelectionDataModelOps(part.surfaceId, action);
  if (ops.length === 0) {
    return part;
  }
  return {
    ...part,
    messages: [...part.messages, ...ops],
  };
}
