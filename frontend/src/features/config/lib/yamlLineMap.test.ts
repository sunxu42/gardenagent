import { describe, expect, it } from "vitest";
import { buildYamlLineIndex, resolvePathRange } from "./yamlLineMap";

const SAMPLE = `meta:
  language: zh
system:
  identity: hello
  rules:
  - rule one
  - rule two
speech_examples:
- id: ex1
  user: hi
  assistant: hey
`;

describe("yamlLineMap", () => {
  it("maps nested keys and list blocks", () => {
    const index = buildYamlLineIndex(SAMPLE);
    const identity = resolvePathRange(index, "system.identity");
    expect(identity?.startLine).toBe(3);

    const rules = resolvePathRange(index, "system.rules");
    expect(rules).toBeDefined();
    expect(rules!.endLine).toBeGreaterThan(rules!.startLine);

    const user = resolvePathRange(index, "speech_examples.0.user");
    expect(user).toBeDefined();
  });

  it("maps root sections", () => {
    const index = buildYamlLineIndex(SAMPLE);
    expect(index.rootRanges.has("system")).toBe(true);
    expect(index.rootRanges.get("system")!.startLine).toBe(2);
  });
});
