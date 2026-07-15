import { describe, expect, it } from "vitest";
import type { A2uiPart } from "../types";
import { appendSelectionSnapshot, buildSelectionDataModelOps } from "./a2uiSelectionSnapshot";

const basePart: A2uiPart = {
  type: "a2ui",
  surfaceId: "plan-selector",
  status: "ready",
  interaction: "pending",
  messages: [
    {
      version: "v0.9",
      createSurface: { surfaceId: "plan-selector", catalogId: "shadcn" },
    },
    {
      version: "v0.9",
      updateDataModel: { surfaceId: "plan-selector", path: "/selectedPlan", value: null },
    },
  ],
};

describe("a2uiSelectionSnapshot", () => {
  it("builds selectedPlan update from single-select-cards context", () => {
    const ops = buildSelectionDataModelOps("single-select-cards", {
      context: { planId: "plan-a" },
    });
    expect(ops).toHaveLength(1);
    expect(ops[0]).toEqual({
      version: "v0.9",
      updateDataModel: {
        surfaceId: "single-select-cards",
        path: "/selectedPlan",
        value: "plan-a",
      },
    });
  });

  it("builds selectedOption update for single-select", () => {
    const ops = buildSelectionDataModelOps("single-select", {
      context: { optionId: "ocean" },
    });
    expect(ops[0]).toEqual({
      version: "v0.9",
      updateDataModel: {
        surfaceId: "single-select",
        path: "/selectedOption",
        value: "ocean",
      },
    });
  });

  it("builds selectedIds update for multi-select", () => {
    const ops = buildSelectionDataModelOps("multi-select", {
      context: { selectedIds: ["a", "b"] },
    });
    expect(ops[0]).toEqual({
      version: "v0.9",
      updateDataModel: {
        surfaceId: "multi-select",
        path: "/selectedIds",
        value: ["a", "b"],
      },
    });
  });

  it("appends snapshot ops after existing protocol messages", () => {
    const next = appendSelectionSnapshot(basePart, { context: { planId: "plan-a" } });
    expect(next.messages).toHaveLength(3);
    expect(next.messages[2]).toEqual({
      version: "v0.9",
      updateDataModel: {
        surfaceId: "plan-selector",
        path: "/selectedPlan",
        value: "plan-a",
      },
    });
  });
});
