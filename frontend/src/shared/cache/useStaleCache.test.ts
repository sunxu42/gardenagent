import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearAllCaches, writeCache } from "@/shared/cache/cacheStore";
import { clearInFlightRequests } from "@/shared/cache/inFlight";
import {
  DEFAULT_SYNC_MIN_INTERVAL_MS,
  useStaleCache,
} from "@/shared/cache/useStaleCache";

describe("useStaleCache", () => {
  beforeEach(() => {
    sessionStorage.clear();
    clearAllCaches();
    clearInFlightRequests();
  });

  afterEach(() => {
    sessionStorage.clear();
    clearAllCaches();
    clearInFlightRequests();
    vi.restoreAllMocks();
  });

  it("shows initial loading when cache is empty", async () => {
    const fetcher = vi.fn().mockResolvedValue("fresh");

    const { result } = renderHook(() => useStaleCache("test-key", fetcher));

    expect(result.current.isInitialLoading).toBe(true);
    expect(result.current.isSyncing).toBe(false);
    expect(result.current.data).toBeNull();

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
    });

    expect(result.current.data).toBe("fresh");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("shows cached data immediately and syncs in background", async () => {
    writeCache("test-key", "stale");
    const fetcher = vi.fn().mockResolvedValue("fresh");

    const { result } = renderHook(() =>
      useStaleCache("test-key", fetcher, { syncMinIntervalMs: 0 }),
    );

    expect(result.current.isInitialLoading).toBe(false);
    expect(result.current.data).toBe("stale");
    expect(result.current.isSyncing).toBe(true);

    await waitFor(() => {
      expect(result.current.isSyncing).toBe(false);
    });

    expect(result.current.data).toBe("fresh");
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(result.current.syncFailed).toBe(false);
  });

  it("skips sync when cache is still fresh", async () => {
    writeCache("test-key", "cached");
    const fetcher = vi.fn().mockResolvedValue("fresh");

    const { result } = renderHook(() =>
      useStaleCache("test-key", fetcher, {
        syncMinIntervalMs: DEFAULT_SYNC_MIN_INTERVAL_MS,
      }),
    );

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
    });

    expect(result.current.data).toBe("cached");
    expect(result.current.isSyncing).toBe(false);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("keeps cached data when sync fails", async () => {
    writeCache("test-key", "stale");
    const fetcher = vi.fn().mockRejectedValue(new Error("network"));

    const { result } = renderHook(() =>
      useStaleCache("test-key", fetcher, { syncMinIntervalMs: 0 }),
    );

    await waitFor(() => {
      expect(result.current.isSyncing).toBe(false);
    });

    expect(result.current.data).toBe("stale");
    expect(result.current.syncFailed).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("does not show sync failed for shared abort errors", async () => {
    writeCache("dup-key", "stale");
    let rejectFetch: (error: Error) => void = () => {};
    const fetcher = vi.fn(
      () =>
        new Promise<string>((_resolve, reject) => {
          rejectFetch = reject;
        }),
    );

    const hookA = renderHook(() =>
      useStaleCache("dup-key", fetcher, { syncMinIntervalMs: 0 }),
    );
    const hookB = renderHook(() =>
      useStaleCache("dup-key", fetcher, { syncMinIntervalMs: 0 }),
    );

    expect(fetcher).toHaveBeenCalledTimes(1);

    await act(async () => {
      rejectFetch(new DOMException("aborted", "AbortError"));
    });

    await waitFor(() => {
      expect(hookA.result.current.isSyncing).toBe(false);
      expect(hookB.result.current.isSyncing).toBe(false);
    });

    expect(hookA.result.current.syncFailed).toBe(false);
    expect(hookB.result.current.syncFailed).toBe(false);
    expect(hookA.result.current.data).toBe("stale");
    expect(hookB.result.current.data).toBe("stale");
  });

  it("sets error when first load fails without cache", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useStaleCache("test-key", fetcher));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("network");
  });

  it("deduplicates concurrent fetches for the same key", async () => {
    let resolveFetch: (value: string) => void = () => {};
    const fetcher = vi.fn(
      () =>
        new Promise<string>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    const hookA = renderHook(() => useStaleCache("dup-key", fetcher));
    const hookB = renderHook(() => useStaleCache("dup-key", fetcher));

    expect(fetcher).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveFetch("ok");
    });

    await waitFor(() => {
      expect(hookA.result.current.data).toBe("ok");
      expect(hookB.result.current.data).toBe("ok");
    });
  });
});
