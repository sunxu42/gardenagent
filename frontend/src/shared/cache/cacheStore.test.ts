import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  clearAllCaches,
  clearMemoryCache,
  readCache,
  writeCache,
} from "@/shared/cache/cacheStore";

describe("cacheStore", () => {
  beforeEach(() => {
    sessionStorage.clear();
    clearAllCaches();
  });

  afterEach(() => {
    sessionStorage.clear();
    clearAllCaches();
  });

  it("returns null when cache is empty", () => {
    expect(readCache<string>("missing")).toBeNull();
  });

  it("writes and reads from memory", () => {
    writeCache("prompt-tree", [{ name: "soul.yaml" }]);
    expect(readCache("prompt-tree")).toEqual([{ name: "soul.yaml" }]);
  });

  it("persists to sessionStorage with prefix", () => {
    writeCache("scenarios", [{ id: "a" }]);
    expect(sessionStorage.getItem("gardenagent:cache:scenarios")).toContain('"id":"a"');
  });

  it("hydrates memory from sessionStorage on read", () => {
    sessionStorage.setItem(
      "gardenagent:cache:scenarios",
      JSON.stringify({ data: [{ id: "b" }], fetchedAt: 1 }),
    );
    clearMemoryCache();
    expect(readCache<Array<{ id: string }>>("scenarios")).toEqual([{ id: "b" }]);
  });

  it("returns null for corrupted sessionStorage JSON", () => {
    sessionStorage.setItem("gardenagent:cache:scenarios", "not-json");
    expect(readCache("scenarios")).toBeNull();
  });
});
