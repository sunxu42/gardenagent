import { useEffect, useMemo, useState } from "react";
import type { ComponentAdapterProps } from "a2ui-shadcn";
import { isAfter, isBefore, startOfDay } from "date-fns";
import { zhCN } from "react-day-picker/locale";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";
import {
  clampDate,
  dateToParts,
  formatDisplayDate,
  parseIsoDate,
  partsToDate,
  todayParts,
  toIsoDate,
  yearRange,
  type DateParts,
} from "../lib/datePickerUtils";
import { a2uiApplePressable } from "./a2uiAppleClasses";

const SELECTED_DATE_PATH = "/selectedDate";

export function DatePicker({
  component,
  dataModel,
  surfaceId,
  onAction,
  resolveValue,
}: ComponentAdapterProps) {
  const minDate = String(resolveValue(component.minDate as string | undefined, ""));
  const maxDate = String(resolveValue(component.maxDate as string | undefined, ""));
  const defaultDate = String(resolveValue(component.defaultDate as string | undefined, ""));
  const confirmLabel = String(resolveValue(component.confirmLabel as string | undefined, "确认日期"));
  const [isConfirmed, setIsConfirmed] = useState(false);

  const initialParts = useMemo(
    () => clampDate(parseIsoDate(defaultDate) ?? todayParts(), minDate, maxDate),
    [defaultDate, minDate, maxDate],
  );

  const [parts, setParts] = useState<DateParts>(initialParts);
  const [calendarMonth, setCalendarMonth] = useState(() => partsToDate(initialParts));

  useEffect(() => {
    setParts(initialParts);
    setCalendarMonth(partsToDate(initialParts));
  }, [initialParts]);

  useEffect(() => {
    const syncSelected = () => {
      setIsConfirmed(Boolean(dataModel.get(SELECTED_DATE_PATH)));
    };
    syncSelected();
    return dataModel.subscribe(SELECTED_DATE_PATH, syncSelected);
  }, [dataModel]);

  const selectedDate = useMemo(() => partsToDate(parts), [parts]);
  const display = formatDisplayDate(parts);
  const { minYear, maxYear } = yearRange(minDate, maxDate);
  const startMonth = useMemo(() => new Date(minYear, 0, 1), [minYear]);
  const endMonth = useMemo(() => new Date(maxYear, 11, 31), [maxYear]);
  const minBoundary = useMemo(
    () => (minDate ? startOfDay(partsToDate(parseIsoDate(minDate)!)) : undefined),
    [minDate],
  );
  const maxBoundary = useMemo(
    () => (maxDate ? startOfDay(partsToDate(parseIsoDate(maxDate)!)) : undefined),
    [maxDate],
  );

  const isDayDisabled = (date: Date) => {
    const day = startOfDay(date);
    if (minBoundary && isBefore(day, minBoundary)) {
      return true;
    }
    if (maxBoundary && isAfter(day, maxBoundary)) {
      return true;
    }
    return false;
  };

  const updateParts = (next: DateParts) => {
    const clamped = clampDate(next, minDate, maxDate);
    setParts(clamped);
    setCalendarMonth(partsToDate(clamped));
  };

  const handleConfirm = () => {
    const action = component.action as
      | {
          event?: {
            name: string;
            context?: Record<string, unknown>;
          };
        }
      | undefined;
    if (!action?.event) {
      return;
    }

    const iso = toIsoDate(parts);
    dataModel.set(SELECTED_DATE_PATH, iso);
    onAction({
      surfaceId,
      sourceComponentId: component.id,
      name: action.event.name,
      context: action.event.context ?? {
        date: iso,
        year: parts.year,
        month: parts.month,
        day: parts.day,
      },
      timestamp: new Date().toISOString(),
    });
  };

  return (
    <div
      className={cn("a2ui-date-picker", isConfirmed && "a2ui-date-picker--confirmed")}
      aria-live="polite"
    >
      <div className="a2ui-date-picker__selection">
        <span className="a2ui-date-picker__selection-date">{display.primary}</span>
        <span className="a2ui-date-picker__selection-weekday">{display.secondary}</span>
      </div>

      <div className="a2ui-date-picker__calendar">
        <Calendar
          mode="single"
          locale={zhCN}
          captionLayout="label"
          showOutsideDays={false}
          fixedWeeks
          selected={selectedDate}
          month={calendarMonth}
          onMonthChange={setCalendarMonth}
          startMonth={startMonth}
          endMonth={endMonth}
          disabled={isConfirmed ? true : isDayDisabled}
          onSelect={(date) => {
            if (!date || isConfirmed) {
              return;
            }
            updateParts(dateToParts(date));
          }}
          formatters={{
            formatCaption: (date) => `${date.getFullYear()}年${date.getMonth() + 1}月`,
          }}
          className="a2ui-date-picker__rdp w-full bg-transparent px-1 py-3 [--cell-size:2.5rem]"
          classNames={{
            root: "w-full",
            months: "relative w-full",
            month: "w-full gap-3",
            month_caption: "mb-2 flex h-10 w-full items-center",
            nav: "flex w-full items-center justify-between gap-2",
            button_previous: "a2ui-date-picker__nav-btn",
            button_next: "a2ui-date-picker__nav-btn",
            caption_label: "a2ui-date-picker__caption pointer-events-none flex-1 text-center",
            weekdays: "a2ui-date-picker__weekdays",
            weekday: "a2ui-date-picker__weekday",
            month_grid: "a2ui-date-picker__month-grid w-full",
            week: "a2ui-date-picker__week",
            day: "a2ui-date-picker__day",
            today: "bg-transparent",
          }}
          buttonVariant="ghost"
        />
      </div>

      <div className="a2ui-date-picker__footer">
        <Button
          type="button"
          disabled={isConfirmed}
          onClick={handleConfirm}
          className={cn(
            "a2ui-confirm-btn a2ui-date-picker__confirm h-11 w-full rounded-[0.875rem]",
            "bg-[var(--a2ui-accent)] px-4 text-[0.9375rem] font-semibold tracking-[-0.01em] text-white",
            "shadow-[0_2px_12px_color-mix(in_srgb,var(--a2ui-accent)_32%,transparent)]",
            "hover:bg-[var(--a2ui-accent)] hover:brightness-105",
            a2uiApplePressable,
          )}
        >
          {isConfirmed ? "已确认" : confirmLabel}
        </Button>
      </div>
    </div>
  );
}
