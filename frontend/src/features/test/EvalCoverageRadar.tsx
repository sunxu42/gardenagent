import { useRef, useState } from "react";

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

interface TooltipState {
  domain: string;
  x: number;
  y: number;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function EvalCoverageRadar({
  points,
  selectedDomain,
  onSelectDomain,
  onEnterDomain,
}: EvalCoverageRadarProps): JSX.Element {
  const rings = [0.25, 0.5, 0.75, 1];
  const chartWrapRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const hoveredPoint = tooltip
    ? (points.find((point) => point.domain === tooltip.domain) ?? null)
    : null;

  const updateTooltip = (domain: string, clientX: number, clientY: number): void => {
    const wrap = chartWrapRef.current;
    if (!wrap) {
      return;
    }
    const rect = wrap.getBoundingClientRect();
    setTooltip({
      domain,
      x: clientX - rect.left + 10,
      y: clientY - rect.top + 10,
    });
  };

  const clearTooltip = (): void => {
    setTooltip(null);
  };

  return (
    <div className="eval-coverage-radar">
      <div
        ref={chartWrapRef}
        className="eval-coverage-radar__chart-wrap"
        onMouseLeave={clearTooltip}
      >
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
              <path
                key={`${point.domain}-sector`}
                className={`eval-coverage-radar__sector${
                  selected ? " eval-coverage-radar__sector--selected" : ""
                }`}
                d={sectorPath(CENTER, RADIUS, index, points.length)}
                onMouseEnter={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
                onMouseMove={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
              />
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
                  onMouseEnter={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
                  onMouseMove={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
                />
                <circle
                  className={`eval-coverage-radar__vertex eval-coverage-radar__vertex--pass${
                    selected ? " eval-coverage-radar__vertex--selected" : ""
                  }`}
                  cx={pass.x}
                  cy={pass.y}
                  r={selected ? 5 : 3.5}
                  onClick={() => onSelectDomain(point.domain)}
                  onMouseEnter={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
                  onMouseMove={(event) => updateTooltip(point.domain, event.clientX, event.clientY)}
                />
              </g>
            );
          })}
        </svg>

        {hoveredPoint ? (
          <div
            className="eval-coverage-radar__tooltip"
            role="tooltip"
            style={{ left: tooltip?.x ?? 0, top: tooltip?.y ?? 0 }}
          >
            <p className="eval-coverage-radar__tooltip-title">{hoveredPoint.domain_label}</p>
            <p className="eval-coverage-radar__tooltip-metric">
              <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--coverage" />
              场景覆盖 {formatPercent(hoveredPoint.coverage_score)}
            </p>
            <p className="eval-coverage-radar__tooltip-metric">
              <span className="eval-coverage-radar__swatch eval-coverage-radar__swatch--pass" />
              通过率 {formatPercent(hoveredPoint.pass_score)}
            </p>
          </div>
        ) : null}
      </div>

      <div className="eval-coverage-radar__domains">
        {points.map((point) => {
          const selected = selectedDomain === point.domain;
          return (
            <button
              key={point.domain}
              aria-pressed={selected}
              className={`eval-coverage-radar__domain-btn${
                selected ? " eval-coverage-radar__domain-btn--selected" : ""
              }`}
              type="button"
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
            </button>
          );
        })}
      </div>
    </div>
  );
}
