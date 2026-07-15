import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { DomainRadarPoint } from "@/features/test/coverageRadarModel";
import { polarPoint, polygonPoints, sectorPath } from "@/features/test/coverageRadarModel";

const VIEW_SIZE = 360;
const CENTER = VIEW_SIZE / 2;
const RADIUS = 118;
const LABEL_RADIUS = RADIUS + 34;

interface EvalCoverageRadarProps {
  points: DomainRadarPoint[];
  selectedDomain: string | null;
  onSelectDomain: (domain: string) => void;
  onEnterDomain?: (domain: string) => void;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function DomainTooltipContent({ point }: { point: DomainRadarPoint }): JSX.Element {
  return (
    <div>
      <p className="eval-coverage-radar__tooltip-title">{point.domain_label}</p>
      <p className="eval-coverage-radar__tooltip-metric">
        <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--coverage" />
        场景覆盖 {formatPercent(point.coverage_score)}
      </p>
      <p className="eval-coverage-radar__tooltip-metric">
        <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--pass" />
        通过率 {formatPercent(point.pass_score)}
      </p>
    </div>
  );
}

export function EvalCoverageRadar({
  points,
  selectedDomain,
  onSelectDomain,
  onEnterDomain,
}: EvalCoverageRadarProps): JSX.Element {
  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <TooltipProvider delayDuration={0}>
      <div className="eval-coverage-radar">
        <div className="eval-coverage-radar__chart-wrap">
          <div aria-hidden className="eval-coverage-radar__legend">
            <span className="eval-coverage-radar__legend-item">
              <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--coverage" />
              场景覆盖
            </span>
            <span className="eval-coverage-radar__legend-item">
              <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--pass" />
              通过率
            </span>
          </div>

          <svg
            aria-label="评测能力域雷达图"
            className="eval-coverage-radar__chart"
            role="img"
            viewBox={`0 0 ${VIEW_SIZE} ${VIEW_SIZE}`}
          >
            {rings.map((ring) => (
              <circle
                key={ring}
                className="eval-coverage-radar__ring"
                cx={CENTER}
                cy={CENTER}
                fill="none"
                r={RADIUS * ring}
              />
            ))}

            {points.map((point, index) => {
              const selected = selectedDomain === point.domain;
              return (
                <Tooltip key={`${point.domain}-sector`}>
                  <TooltipTrigger asChild>
                    <g className="eval-coverage-radar__sector-hit">
                      <path
                        className={`eval-coverage-radar__sector${
                          selected ? " eval-coverage-radar__sector--selected" : ""
                        }`}
                        d={sectorPath(CENTER, RADIUS, index, points.length)}
                        onClick={() => onSelectDomain(point.domain)}
                      />
                    </g>
                  </TooltipTrigger>
                  <TooltipContent className="eval-coverage-radar__tooltip border-border/45 p-2 shadow-md">
                    <DomainTooltipContent point={point} />
                  </TooltipContent>
                </Tooltip>
              );
            })}

            {points.map((point, index) => {
              const outer = polarPoint(CENTER, LABEL_RADIUS, index, points.length, 1);
              const axisEnd = polarPoint(CENTER, RADIUS, index, points.length, 1);
              const selected = selectedDomain === point.domain;
              return (
                <g key={point.domain}>
                  <line
                    className={`eval-coverage-radar__axis${selected ? " eval-coverage-radar__axis--selected" : ""}`}
                    x1={CENTER}
                    x2={axisEnd.x}
                    y1={CENTER}
                    y2={axisEnd.y}
                  />
                  <text
                    className={`eval-coverage-radar__label${selected ? " eval-coverage-radar__label--selected" : ""}`}
                    dominantBaseline="middle"
                    textAnchor="middle"
                    x={outer.x}
                    y={outer.y}
                  >
                    {point.domain_label}
                  </text>
                </g>
              );
            })}

            <polygon
              className="eval-coverage-radar__area eval-coverage-radar__area--coverage"
              points={polygonPoints(CENTER, RADIUS, points, "coverage_score")}
            />
            <polygon
              className="eval-coverage-radar__line eval-coverage-radar__line--coverage"
              fill="none"
              points={polygonPoints(CENTER, RADIUS, points, "coverage_score")}
            />

            <polygon
              className="eval-coverage-radar__area eval-coverage-radar__area--pass"
              points={polygonPoints(CENTER, RADIUS, points, "pass_score")}
            />
            <polygon
              className="eval-coverage-radar__line eval-coverage-radar__line--pass"
              fill="none"
              points={polygonPoints(CENTER, RADIUS, points, "pass_score")}
            />

            {points.map((point, index) => {
              const coverage = polarPoint(CENTER, RADIUS, index, points.length, point.coverage_score);
              const pass = polarPoint(CENTER, RADIUS, index, points.length, point.pass_score);
              const selected = selectedDomain === point.domain;
              return (
                <g key={`${point.domain}-handles`}>
                  <circle
                    className={`eval-coverage-radar__vertex eval-coverage-radar__vertex--coverage${
                      selected ? " eval-coverage-radar__vertex--selected" : ""
                    }`}
                    cx={coverage.x}
                    cy={coverage.y}
                    r={selected ? 5 : 3.5}
                    onClick={() => onSelectDomain(point.domain)}
                  />
                  <circle
                    className={`eval-coverage-radar__vertex eval-coverage-radar__vertex--pass${
                      selected ? " eval-coverage-radar__vertex--selected" : ""
                    }`}
                    cx={pass.x}
                    cy={pass.y}
                    r={selected ? 5 : 3.5}
                    onClick={() => onSelectDomain(point.domain)}
                  />
                </g>
              );
            })}
          </svg>
        </div>

        <div className="eval-coverage-radar__domains">
          {points.map((point) => {
            const selected = selectedDomain === point.domain;
            return (
              <Button
                key={point.domain}
                type="button"
                variant="ghost"
                aria-pressed={selected}
                className={`eval-coverage-radar__domain-btn h-auto${
                  selected ? " eval-coverage-radar__domain-btn--selected" : ""
                }`}
                onClick={() => {
                  if (onEnterDomain) {
                    onEnterDomain(point.domain);
                    return;
                  }
                  onSelectDomain(point.domain);
                }}
              >
                <span className="eval-coverage-radar__domain-name">{point.domain_label}</span>
                <span className="eval-coverage-radar__domain-metrics">
                  覆盖 {formatPercent(point.coverage_score)} · 通过 {formatPercent(point.pass_score)}
                </span>
              </Button>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
}
