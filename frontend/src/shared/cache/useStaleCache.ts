import { useCallback, useEffect, useRef, useState } from "react";

import { readCache, writeCache } from "@/shared/cache/cacheStore";
import { dedupedFetch } from "@/shared/cache/inFlight";

const SYNC_FAILED_DISPLAY_MS = 3000;

export interface UseStaleCacheOptions {
  enabled?: boolean;
}

export interface UseStaleCacheResult<T> {
  data: T | null;
  isInitialLoading: boolean;
  isSyncing: boolean;
  syncFailed: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useStaleCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: UseStaleCacheOptions,
): UseStaleCacheResult<T> {
  const enabled = options?.enabled ?? true;
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const cachedOnMount = useRef<T | null>(null);
  if (cachedOnMount.current === null) {
    cachedOnMount.current = readCache<T>(key);
  }
  const hasCacheOnMount = cachedOnMount.current !== null;

  const [data, setData] = useState<T | null>(hasCacheOnMount ? cachedOnMount.current : null);
  const [isInitialLoading, setIsInitialLoading] = useState(!hasCacheOnMount);
  const [isSyncing, setIsSyncing] = useState(hasCacheOnMount && enabled);
  const [syncFailed, setSyncFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generationRef = useRef(0);
  const syncFailedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearSyncFailedTimer = useCallback((): void => {
    if (syncFailedTimerRef.current) {
      clearTimeout(syncFailedTimerRef.current);
      syncFailedTimerRef.current = null;
    }
  }, []);

  const showSyncFailedBriefly = useCallback((): void => {
    clearSyncFailedTimer();
    setSyncFailed(true);
    syncFailedTimerRef.current = setTimeout(() => {
      setSyncFailed(false);
      syncFailedTimerRef.current = null;
    }, SYNC_FAILED_DISPLAY_MS);
  }, [clearSyncFailedTimer]);

  const runFetch = useCallback(async (): Promise<void> => {
    const generation = generationRef.current;
    const hadCache = readCache<T>(key) !== null;

    if (hadCache) {
      setIsSyncing(true);
    }
    setSyncFailed(false);
    setError(null);

    try {
      const fresh = await dedupedFetch(key, () => fetcherRef.current());
      if (generation !== generationRef.current) {
        return;
      }
      writeCache(key, fresh);
      setData(fresh);
    } catch (loadError: unknown) {
      if (generation !== generationRef.current) {
        return;
      }
      const message = loadError instanceof Error ? loadError.message : "加载失败";
      if (hadCache) {
        console.warn(`[useStaleCache] sync failed for "${key}":`, message);
        showSyncFailedBriefly();
      } else {
        setError(message);
        setData(null);
      }
    } finally {
      if (generation === generationRef.current) {
        setIsInitialLoading(false);
        setIsSyncing(false);
      }
    }
  }, [key, showSyncFailedBriefly]);

  useEffect(() => {
    generationRef.current += 1;

    const cached = readCache<T>(key);
    if (cached !== null) {
      setData(cached);
      setIsInitialLoading(false);
      setIsSyncing(enabled);
    } else {
      setData(null);
      setIsInitialLoading(true);
      setIsSyncing(false);
    }
    setError(null);
    setSyncFailed(false);

    if (!enabled) {
      setIsSyncing(false);
      setIsInitialLoading(false);
      return () => {
        generationRef.current += 1;
        clearSyncFailedTimer();
      };
    }

    void runFetch();

    return () => {
      generationRef.current += 1;
      clearSyncFailedTimer();
    };
  }, [clearSyncFailedTimer, enabled, key, runFetch]);

  const reload = useCallback(async (): Promise<void> => {
    await runFetch();
  }, [runFetch]);

  return {
    data,
    isInitialLoading,
    isSyncing,
    syncFailed,
    error,
    reload,
  };
}
