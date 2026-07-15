import { ChevronDown } from "lucide-react";
import { useCallback, useId, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import type { AffectLockSlice } from "../../types";
import {
  AFFECT_GUIDE_MOTION_MS,
  captureFlipPositions,
  runFlipAnimation,
} from "../../lib/affectGuideMotion";

export interface AffectRefReorderItem {
  id: string;
}

interface AffectRefReorderPanelProps<T extends AffectRefReorderItem> {
  items: readonly T[];
  currentId?: string | null;
  affectLock?: AffectLockSlice;
  onToggleLock?: (id: string) => void;
  expandable?: boolean;
  emptyState?: ReactNode;
  renderItem: (item: T, ctx: { current: boolean; locked: boolean; onToggleLock?: () => void }) => ReactNode;
}

function sortWithCurrentFirst<T extends AffectRefReorderItem>(
  items: readonly T[],
  currentId?: string | null,
): T[] {
  if (!currentId) {
    return [...items];
  }
  const current = items.find((item) => item.id === currentId);
  if (!current) {
    return [...items];
  }
  return [current, ...items.filter((item) => item.id !== currentId)];
}

export function AffectRefReorderPanel<T extends AffectRefReorderItem>({
  items,
  currentId,
  affectLock,
  onToggleLock,
  expandable = true,
  emptyState,
  renderItem,
}: AffectRefReorderPanelProps<T>) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const flipRef = useRef<HTMLDivElement>(null);
  const flipSnapshotRef = useRef<Map<string, DOMRect> | null>(null);
  const reorderIntentRef = useRef(false);

  const sorted = useMemo(() => sortWithCurrentFirst(items, currentId), [items, currentId]);
  const head = sorted[0];
  const tail = sorted.slice(1);
  const orderKey = sorted.map((item) => item.id).join("|");

  const handleToggleLock = useCallback(
    (id: string) => {
      if (!onToggleLock) {
        return;
      }
      const unlockingCurrent = id === currentId && affectLock?.locked;
      const lockingOther = id !== currentId;
      if ((lockingOther || unlockingCurrent) && flipRef.current) {
        reorderIntentRef.current = true;
        flipSnapshotRef.current = captureFlipPositions(flipRef.current);
      }
      onToggleLock(id);
    },
    [affectLock?.locked, currentId, onToggleLock],
  );

  useLayoutEffect(() => {
    if (!reorderIntentRef.current || !flipSnapshotRef.current || !flipRef.current) {
      return;
    }
    runFlipAnimation(flipRef.current, flipSnapshotRef.current, AFFECT_GUIDE_MOTION_MS);
    reorderIntentRef.current = false;
    flipSnapshotRef.current = null;
  }, [orderKey, affectLock?.locked, affectLock?.refId]);

  const toggleExpand = useCallback(() => {
    if (!expandable || tail.length === 0) {
      return;
    }
    setOpen((prev) => !prev);
  }, [expandable, tail.length]);

  if (!head) {
    return <div className="text-[11px]">{emptyState ?? null}</div>;
  }

  const isLocked = (id: string) => Boolean(affectLock?.locked && affectLock.refId === id);

  const renderFlipRow = (item: T, current: boolean) => (
    <div key={item.id} data-flip-id={item.id} className="min-w-0">
      {renderItem(item, {
        current,
        locked: isLocked(item.id),
        onToggleLock: onToggleLock ? () => handleToggleLock(item.id) : undefined,
      })}
    </div>
  );

  if (!expandable || tail.length === 0) {
    return (
      <div ref={flipRef} className="text-[11px]">
        {renderFlipRow(head, true)}
      </div>
    );
  }

  return (
    <div ref={flipRef} className="text-[11px]">
      <div className="grid grid-cols-[1.75rem_1fr] items-start gap-x-4">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={toggleExpand}
          aria-expanded={open}
          aria-controls={panelId}
          aria-label={open ? "收起其它项" : "展开其它项"}
          className="mt-2 h-7 w-7 shrink-0 rounded-md shadow-none hover:bg-transparent"
        >
          <ChevronDown
            className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ease-out motion-reduce:transition-none ${
              open ? "rotate-0" : "-rotate-90"
            }`}
            aria-hidden
          />
        </Button>

        <div className="min-w-0 space-y-1 pt-0.5">{renderFlipRow(head, true)}</div>
      </div>

      <div className="grid grid-cols-[1.75rem_1fr] gap-x-4">
        <div />
        <div
          id={panelId}
          className={`grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none ${
            open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
          aria-hidden={!open}
        >
          <div className="overflow-hidden">
            <div className="space-y-1 pt-1">{tail.map((item) => renderFlipRow(item, false))}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
