import { describe, expect, it } from "vitest";
import {
  clampDate,
  dateToParts,
  isDateInRange,
  parseIsoDate,
  partsToDate,
  toIsoDate,
} from "./datePickerUtils";

describe("datePickerUtils", () => {
  it("converts between parts and Date", () => {
    const parts = { year: 2026, month: 7, day: 10 };
    expect(dateToParts(partsToDate(parts))).toEqual(parts);
  });

  it("clamps invalid day to month end", () => {
    const clamped = clampDate({ year: 2026, month: 2, day: 31 }, "", "");
    expect(clamped.day).toBe(28);
    expect(toIsoDate(clamped)).toBe("2026-02-28");
  });

  it("respects min and max date range", () => {
    expect(isDateInRange("2026-07-09", "2026-07-10", "2026-12-31")).toBe(false);
    expect(isDateInRange("2026-07-10", "2026-07-10", "2026-12-31")).toBe(true);
    expect(parseIsoDate("2026-07-10")).toEqual({ year: 2026, month: 7, day: 10 });
  });
});
