import type { CacheEntry } from "@/shared/cache/types";

const STORAGE_PREFIX = "gardenagent:cache:";

const memoryCache = new Map<string, unknown>();

function toStorageKey(key: string): string {
  return `${STORAGE_PREFIX}${key}`;
}

export function readCache<T>(key: string): T | null {
  if (memoryCache.has(key)) {
    return memoryCache.get(key) as T;
  }

  try {
    const raw = sessionStorage.getItem(toStorageKey(key));
    if (!raw) {
      return null;
    }
    const entry = JSON.parse(raw) as CacheEntry<T>;
    memoryCache.set(key, entry.data);
    return entry.data;
  } catch {
    return null;
  }
}

export function writeCache<T>(key: string, data: T): void {
  memoryCache.set(key, data);
  try {
    const entry: CacheEntry<T> = { data, fetchedAt: Date.now() };
    sessionStorage.setItem(toStorageKey(key), JSON.stringify(entry));
  } catch {
    // sessionStorage unavailable or quota exceeded
  }
}

export function clearCache(key: string): void {
  memoryCache.delete(key);
  try {
    sessionStorage.removeItem(toStorageKey(key));
  } catch {
    // ignore
  }
}

/** 测试辅助：清空内存层；sessionStorage 由测试自行 clear */
export function clearMemoryCache(): void {
  memoryCache.clear();
}

export function clearAllCaches(): void {
  memoryCache.clear();
  try {
    const keysToRemove: string[] = [];
    for (let index = 0; index < sessionStorage.length; index += 1) {
      const storageKey = sessionStorage.key(index);
      if (storageKey?.startsWith(STORAGE_PREFIX)) {
        keysToRemove.push(storageKey);
      }
    }
    for (const storageKey of keysToRemove) {
      sessionStorage.removeItem(storageKey);
    }
  } catch {
    // ignore
  }
}
