export interface DateParts {
  year: number;
  month: number;
  day: number;
}

export function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

export function parseIsoDate(iso: string): DateParts | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!match) {
    return null;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) {
    return null;
  }
  return { year, month, day };
}

export function toIsoDate(parts: DateParts): string {
  return `${parts.year}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")}`;
}

export function partsToDate(parts: DateParts): Date {
  return new Date(parts.year, parts.month - 1, parts.day);
}

export function dateToParts(date: Date): DateParts {
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
  };
}

export function todayParts(): DateParts {
  const now = new Date();
  return dateToParts(now);
}

export function compareIso(left: string, right: string): number {
  if (left === right) {
    return 0;
  }
  return left < right ? -1 : 1;
}

export function isDateInRange(iso: string, minDate: string, maxDate: string): boolean {
  if (minDate && compareIso(iso, minDate) < 0) {
    return false;
  }
  if (maxDate && compareIso(iso, maxDate) > 0) {
    return false;
  }
  return true;
}

export function clampDate(parts: DateParts, minDate: string, maxDate: string): DateParts {
  const iso = toIsoDate(parts);
  if (minDate && compareIso(iso, minDate) < 0) {
    const parsed = parseIsoDate(minDate);
    if (parsed) {
      return parsed;
    }
  }
  if (maxDate && compareIso(iso, maxDate) > 0) {
    const parsed = parseIsoDate(maxDate);
    if (parsed) {
      return parsed;
    }
  }
  const maxDay = daysInMonth(parts.year, parts.month);
  if (parts.day > maxDay) {
    return { ...parts, day: maxDay };
  }
  return parts;
}

export function yearRange(minDate: string, maxDate: string): { minYear: number; maxYear: number } {
  const currentYear = todayParts().year;
  const minYear = minDate ? (parseIsoDate(minDate)?.year ?? currentYear - 100) : currentYear - 100;
  const maxYear = maxDate ? (parseIsoDate(maxDate)?.year ?? currentYear + 10) : currentYear + 10;
  return { minYear: Math.min(minYear, maxYear), maxYear: Math.max(minYear, maxYear) };
}

export function formatDisplayDate(parts: DateParts): { primary: string; secondary: string } {
  const date = partsToDate(parts);
  const weekday = new Intl.DateTimeFormat("zh-CN", { weekday: "long" }).format(date);
  return {
    primary: `${parts.year}年${parts.month}月${parts.day}日`,
    secondary: weekday,
  };
}

