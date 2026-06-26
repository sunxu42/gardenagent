import { useCallback } from "react";

import type { CoverageMatrix } from "@/features/test/types";
import { CACHE_KEYS } from "@/shared/cache/cacheKeys";
import { useStaleCache } from "@/shared/cache/useStaleCache";
import { fetchCoverage } from "@/services/eval/coverageApi";

export interface CoverageReloadOptions {
  silent?: boolean;
}

export interface CoverageMatrixState {
  matrix: CoverageMatrix | null;
  loading: boolean;
  error: string | null;
  reload: (options?: CoverageReloadOptions) => Promise<void>;
}

export function useCoverageMatrix(): CoverageMatrixState {
  const { data, isInitialLoading, error, reload } = useStaleCache(
    CACHE_KEYS.coverage,
    ({ signal }) => fetchCoverage(signal),
  );

  const reloadCoverage = useCallback(
    async (_options?: CoverageReloadOptions): Promise<void> => {
      await reload({ force: true });
    },
    [reload],
  );

  return {
    matrix: data,
    loading: isInitialLoading,
    error,
    reload: reloadCoverage,
  };
}
