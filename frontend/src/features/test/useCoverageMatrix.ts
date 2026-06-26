import { useCallback, useEffect, useState } from "react";

import type { CoverageMatrix } from "@/features/test/types";
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
  const [matrix, setMatrix] = useState<CoverageMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (options?: CoverageReloadOptions): Promise<void> => {
    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await fetchCoverage();
      setMatrix(data);
    } catch (loadError: unknown) {
      setError(loadError instanceof Error ? loadError.message : "加载覆盖数据失败");
      if (!options?.silent) {
        setMatrix(null);
      }
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { matrix, loading, error, reload };
}
