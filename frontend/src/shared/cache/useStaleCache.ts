import { useCallback, useEffect, useRef, useState } from "react";

import { isCacheFresh, readCache, writeCache } from "@/shared/cache/cacheStore";
import { dedupedFetch, isAbortError } from "@/shared/cache/inFlight";

const SYNC_FAILED_DISPLAY_MS = 3000;
export const DEFAULT_SYNC_MIN_INTERVAL_MS = 30_000;

export interface CacheFetchContext {
  signal: AbortSignal;
}

export type CacheFetcher<T> = (context: CacheFetchContext) => Promise<T>;

export interface UseStaleCacheOptions {
  enabled?: boolean;
  syncMinIntervalMs?: number;
}

export interface ReloadOptions {
  force?: boolean;
}

export interface UseStaleCacheResult<T> {
  data: T | null;
  isInitialLoading: boolean;
  isSyncing: boolean;
  syncFailed: boolean;
  error: string | null;
  reload: (options?: ReloadOptions) => Promise<void>;
}

export function useStaleCache<T>(
  key: string,
  fetcher: CacheFetcher<T>,
  options?: UseStaleCacheOptions,
): UseStaleCacheResult<T> {
  const enabled = options?.enabled ?? true;
  const syncMinIntervalMs = options?.syncMinIntervalMs ?? DEFAULT_SYNC_MIN_INTERVAL_MS;
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const syncMinIntervalRef = useRef(syncMinIntervalMs);
  syncMinIntervalRef.current = syncMinIntervalMs;

  const cachedOnMount = useRef<T | null>(null);
  if (cachedOnMount.current === null) {
    cachedOnMount.current = readCache<T>(key);
  }
  const hasCacheOnMount = cachedOnMount.current !== null;
  const cacheFreshOnMount = hasCacheOnMount && isCacheFresh(key, syncMinIntervalMs);

  const [data, setData] = useState<T | null>(hasCacheOnMount ? cachedOnMount.current : null);
  const [isInitialLoading, setIsInitialLoading] = useState(!hasCacheOnMount);
  const [isSyncing, setIsSyncing] = useState(hasCacheOnMount && enabled && !cacheFreshOnMount);
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

  const runFetch = useCallback(
    async (fetchOptions?: ReloadOptions): Promise<void> => {
      const generation = generationRef.current;
      const hadCache = readCache<T>(key) !== null;
      const minInterval = syncMinIntervalRef.current;

      if (!fetchOptions?.force && hadCache && isCacheFresh(key, minInterval)) {
        setIsInitialLoading(false);
        setIsSyncing(false);
        return;
      }

      if (hadCache) {
        setIsSyncing(true);
      }
      setSyncFailed(false);
      setError(null);

      try {
        const fresh = await dedupedFetch(key, () =>
          fetcherRef.current({ signal: new AbortController().signal }),
        );
        if (generation !== generationRef.current) {
          return;
        }
        writeCache(key, fresh);
        setData(fresh);
      } catch (loadError: unknown) {
        if (generation !== generationRef.current || isAbortError(loadError)) {
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
    },
    [key, showSyncFailedBriefly],
  );

  useEffect(() => {
    generationRef.current += 1;

    const cached = readCache<T>(key);
    const fresh = cached !== null && isCacheFresh(key, syncMinIntervalRef.current);
    if (cached !== null) {
      setData(cached);
      setIsInitialLoading(false);
      setIsSyncing(enabled && !fresh);
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

    if (!fresh) {
      void runFetch();
    }

    return () => {
      generationRef.current += 1;
      clearSyncFailedTimer();
    };
  }, [clearSyncFailedTimer, enabled, key, runFetch]);

  const reload = useCallback(
    async (reloadOptions?: ReloadOptions): Promise<void> => {
      await runFetch(reloadOptions);
    },
    [runFetch],
  );

  return {
    data,
    isInitialLoading,
    isSyncing,
    syncFailed,
    error,
    reload,
  };
}
