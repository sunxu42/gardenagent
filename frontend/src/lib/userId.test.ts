import { describe, it, expect, beforeEach } from "vitest";
import {
  USER_ID_STORAGE_KEY,
  LEGACY_CLIENT_STORAGE_KEY,
  generateUserId,
  validateUserId,
  getOrCreateUserId,
  rotateUserId,
} from "./userId";

describe("userId", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("generateUserId matches pattern", () => {
    expect(validateUserId(generateUserId())).toBe(true);
  });

  it("getOrCreateUserId persists", () => {
    const a = getOrCreateUserId();
    const b = getOrCreateUserId();
    expect(a).toBe(b);
    expect(localStorage.getItem(USER_ID_STORAGE_KEY)).toBe(a);
  });

  it("migrates legacy client.v1", () => {
    localStorage.setItem(
      LEGACY_CLIENT_STORAGE_KEY,
      JSON.stringify({ clientId: "user_legacy12345678", deviceId: "x" }),
    );
    const id = getOrCreateUserId();
    expect(id).toBe("user_legacy12345678");
    expect(localStorage.getItem(LEGACY_CLIENT_STORAGE_KEY)).toBeNull();
  });

  it("rotateUserId returns new id", () => {
    const old = getOrCreateUserId();
    const neu = rotateUserId();
    expect(neu).not.toBe(old);
    expect(localStorage.getItem(USER_ID_STORAGE_KEY)).toBe(neu);
  });
});
