import { useMemo } from "react";

import { EvalCoverageMatrix } from "@/features/test/EvalCoverageMatrix";
import { EvalDomainWorkspace } from "@/features/test/EvalDomainWorkspace";
import { buildDomainRadarPoints } from "@/features/test/coverageRadarModel";
import type { CoverageMatrixState } from "@/features/test/useCoverageMatrix";
import type { PanelView } from "@/features/test/types";
import { isDomainPanelView } from "@/features/test/types";

interface EvalOverviewViewProps {
  panelView: PanelView;
  selectedDomainId: string | null;
  coverage: CoverageMatrixState;
  onSelectDomain: (domainId: string) => void;
  onEnterDomain: (domainId: string) => void;
  onBackToRadar: () => void;
}

export function EvalOverviewView({
  panelView,
  selectedDomainId,
  coverage,
  onSelectDomain,
  onEnterDomain,
  onBackToRadar,
}: EvalOverviewViewProps): JSX.Element {
  const radarPoints = useMemo(
    () => buildDomainRadarPoints(coverage.matrix?.cells ?? []),
    [coverage.matrix?.cells],
  );

  if (isDomainPanelView(panelView)) {
    const point = radarPoints.find((item) => item.domain === panelView.domainId);
    return (
      <EvalDomainWorkspace
        coverageScore={point?.coverage_score ?? 0}
        domainId={panelView.domainId}
        domainLabel={point?.domain_label ?? panelView.domainId}
        passScore={point?.pass_score ?? 0}
        onBack={onBackToRadar}
      />
    );
  }

  return (
    <EvalCoverageMatrix
      matrix={coverage.matrix}
      loading={coverage.loading}
      error={coverage.error}
      onReload={() => void coverage.reload()}
      selectedDomain={selectedDomainId}
      onEnterDomain={onEnterDomain}
      onSelectDomain={onSelectDomain}
    />
  );
}
