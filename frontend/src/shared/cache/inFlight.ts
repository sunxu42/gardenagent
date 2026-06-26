const inFlightRequests = new Map<string, Promise<unknown>>();

export function dedupedFetch<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const existing = inFlightRequests.get(key);
  if (existing) {
    return existing as Promise<T>;
  }

  const promise = fetcher().finally(() => {
    inFlightRequests.delete(key);
  });
  inFlightRequests.set(key, promise);
  return promise;
}

/** 测试辅助 */
export function clearInFlightRequests(): void {
  inFlightRequests.clear();
}

export function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") {
    return true;
  }
  return error instanceof Error && error.name === "AbortError";
}
