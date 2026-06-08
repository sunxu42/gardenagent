import { describe, expect, it } from "vitest";
import {
  addChildToMap,
  insertRootSiblingAfter,
  objectToTree,
  renameNodeKey,
  treeToObject,
} from "./soulYamlTree";

describe("soulYamlTree", () => {
  it("roundtrips nested structure", () => {
    const obj = {
      system: { identity: "hello", rules: ["a", "b"] },
      format: "voice",
    };
    const roots = objectToTree(obj);
    expect(roots.find((n) => n.key === "system")?.nodeType).toBe("map");
    const back = treeToObject(roots);
    expect(back).toEqual(obj);
  });

  it("renames nested keys and updates ids", () => {
    const roots = objectToTree({ system: { identity: "hi" } });
    const system = roots.find((n) => n.key === "system")!;
    const next = renameNodeKey(roots, system.children![0].id, "who");
    const back = treeToObject(next);
    expect(back).toEqual({ system: { who: "hi" } });
    expect(next[0].children?.[0].id).toBe("system.who");
  });

  it("inserts root sibling and child field", () => {
    const roots = objectToTree({ a: "1" });
    const { roots: after, newNodeId } = insertRootSiblingAfter(roots, "a");
    expect(after.map((n) => n.key)).toEqual(["a", "new_section"]);
    expect(newNodeId).toBe("new_section");

    const mapRoots = objectToTree({ block: { x: 1 } });
    const block = mapRoots[0];
    const { roots: withChild, newNodeId: childId } = addChildToMap(mapRoots, block.id);
    expect(childId).toBe("block.new_field");
    expect(treeToObject(withChild)).toEqual({ block: { x: "1", new_field: "" } });
  });

  it("represents object lists as branches", () => {
    const obj = {
      speech_examples: [{ id: "x", user: "u", assistant: "a" }],
    };
    const roots = objectToTree(obj);
    const block = roots[0];
    expect(block.nodeType).toBe("objectList");
    expect(block.children?.[0].nodeType).toBe("map");
    expect(block.children?.[0].children?.some((c) => c.key === "user")).toBe(true);
  });
});
