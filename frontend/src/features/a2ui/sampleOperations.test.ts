import { describe, expect, it } from "vitest";
import { buildSampleOperations, resolveSurfaceIdFromOperations } from "./sampleOperations";

describe("buildSampleOperations", () => {
  it("builds single_select cards_plans operations", () => {
    const ops = buildSampleOperations("single_select", "cards_plans");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe(
      "single-select-cards",
    );
    expect(ops.length).toBeGreaterThanOrEqual(2);
  });

  it("builds single_select binary_continue operations", () => {
    const ops = buildSampleOperations("single_select", "binary_continue");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe(
      "single-select-binary",
    );
  });

  it("builds single_select emoji_mood operations", () => {
    const ops = buildSampleOperations("single_select", "emoji_mood");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe(
      "single-select-emoji",
    );
    expect(ops.length).toBe(3);
  });

  it("builds single_select default_list operations", () => {
    const ops = buildSampleOperations("single_select", "default_list");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe("single-select");
    expect(ops.length).toBe(3);
  });

  it("builds multi_select animals_3 operations", () => {
    const ops = buildSampleOperations("multi_select", "animals_3");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe("multi-select");
  });

  it("builds date_picker birthday operations", () => {
    const ops = buildSampleOperations("date_picker", "birthday");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe("date-picker");
    expect(ops.length).toBe(3);
  });

  it("builds data_table compare_readonly operations", () => {
    const ops = buildSampleOperations("data_table", "compare_readonly");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe("data-table");
  });

  it("builds data_table pick_day interactive operations", () => {
    const ops = buildSampleOperations("data_table", "pick_day");
    const first = ops[0];
    expect("createSurface" in first && first.createSurface?.surfaceId).toBe("data-table-select");
    expect(ops.length).toBe(3);
    expect(resolveSurfaceIdFromOperations(ops)).toBe("data-table-select");
  });
});
