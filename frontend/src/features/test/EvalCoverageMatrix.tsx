import { RefreshCw } from "lucide-react";
import { useMemo } from "react";

import { PanelEmpty } from "@/components/panel/PanelEmpty";
import { PanelLoading } from "@/components/panel/PanelLoading";
import { EvalCoverageRadar } from "@/features/test/EvalCoverageRadar";
import { EvalDomainSummary } from "@/features/test/EvalDomainSummary";
import { buildDomainRadarPoints } from "@/features/test/coverageRadarModel";
import type { CoverageMatrix } from "@/features/test/types";

interface EvalCoverageMatrixProps {
  matrix: CoverageMatrix | null;
  loading: boolean;
  error: string | null;
  onReload: () => void;
  selectedDomain: string | null;
  onSelectDomain: (domainId: string) => void;
  onEnterDomain: (domainId: string) => void;
}

export function EvalCoverageMatrix({
  matrix,
  loading,
  error,
  onReload,
  selectedDomain,
  onSelectDomain,
  onEnterDomain,
}: EvalCoverageMatrixProps): JSX.Element {
  const radarPoints = useMemo(
    () => buildDomainRadarPoints(matrix?.cells ?? []),
    [matrix?.cells],
  );

  const selectedPoint = useMemo(() => {
    if (!selectedDomain) {
      return null;
    }
    return radarPoints.find((point) => point.domain === selectedDomain) ?? null;
  }, [radarPoints, selectedDomain]);

  if (loading) {
    return <PanelLoading label="加载评测总览…" />;
  }

  if (error) {
    return (
      <PanelEmpty
        title="加载失败"
        description={error}
        action={
          <button className="panel-state__action" type="button" onClick={onReload}>
            <RefreshCw className="h-3 w-3" aria-hidden />
            重试
          </button>
        }
      />
    );
  }

  return (
    <div className="test-sidebar-group min-h-0 flex-1">
      <div className="test-list-panel eval-coverage-radar-panel">
        <EvalCoverageRadar
          points={radarPoints}
          selectedDomain={selectedDomain}
          onEnterDomain={onEnterDomain}
          onSelectDomain={onSelectDomain}
        />
      </div>
      <div className="test-detail-panel">
        <EvalDomainSummary
          point={selectedPoint}
          onEnter={() => {
            if (selectedPoint) {
              onEnterDomain(selectedPoint.domain);
            }
          }}
        />
      </div>
    </div>
  );
}
