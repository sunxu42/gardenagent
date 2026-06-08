import { useId, useMemo } from "react";
import type { VadPoint } from "../types";
import {
  AXIS_LABELS,
  amplifyVadDelta,
  deltaColor,
  polygonPathFromVertices,
  vadVertices,
} from "../lib/vadRadarUtils";

export interface VadRadarLayer {
  point: VadPoint;
  stroke: string;
  fill: string;
  strokeWidth?: number;
  fillOpacity?: number;
}

interface VadRadarChartProps {
  size?: number;
  layers?: VadRadarLayer[];
  /** 与 prev 对比时，按维度 Δ 给 current 描边着色（红升绿降） */
  compareDelta?: VadPoint;
  amplifyDeltaFactor?: number;
  minVisualDelta?: number;
  showLabels?: boolean;
  className?: string;
}

function gridLevels(): number[] {
  return [0.25, 0.5, 0.75, 1];
}

export function VadRadarChart({
  size = 120,
  layers = [],
  compareDelta,
  amplifyDeltaFactor = 2.2,
  minVisualDelta = 0.02,
  showLabels = false,
  className = "",
}: VadRadarChartProps) {
  const uid = useId().replace(/:/g, "");
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.36;
  const labelR = size * 0.46;

  const gridPaths = useMemo(() => {
    return gridLevels().map((level) => {
      const r = maxR * level;
      const verts: [number, number][] = [
        [cx, cy - r],
        [cx + r * Math.cos(Math.PI / 6), cy + r * Math.sin(Math.PI / 6)],
        [cx + r * Math.cos((5 * Math.PI) / 6), cy + r * Math.sin((5 * Math.PI) / 6)],
      ];
      return polygonPathFromVertices(verts);
    });
  }, [cx, cy, maxR]);

  const axisLines = useMemo(() => {
    const outer: [number, number][] = [
      [cx, cy - maxR],
      [cx + maxR * Math.cos(Math.PI / 6), cy + maxR * Math.sin(Math.PI / 6)],
      [cx + maxR * Math.cos((5 * Math.PI) / 6), cy + maxR * Math.sin((5 * Math.PI) / 6)],
    ];
    return outer.map(([x, y]) => ({ x1: cx, y1: cy, x2: x, y2: y }));
  }, [cx, cy, maxR]);

  const labelPositions = useMemo(() => {
    const angles = [-Math.PI / 2, Math.PI / 6, (5 * Math.PI) / 6];
    return AXIS_LABELS.map((label, i) => ({
      label,
      x: cx + labelR * Math.cos(angles[i]),
      y: cy + labelR * Math.sin(angles[i]),
    }));
  }, [cx, cy, labelR]);

  const compareLayer = layers.length >= 2 && compareDelta ? layers[1] : null;
  const comparePrev = layers.length >= 2 ? layers[0] : null;
  const compareCurrentVisualPoint =
    compareLayer && comparePrev && compareDelta
      ? amplifyVadDelta(comparePrev.point, compareLayer.point, amplifyDeltaFactor, minVisualDelta)
      : compareLayer?.point ?? null;

  const compareEdges = useMemo(() => {
    if (!compareCurrentVisualPoint || !compareDelta) return null;
    const verts = vadVertices(compareCurrentVisualPoint, cx, cy, maxR);
    const deltas = [compareDelta.v, compareDelta.a, compareDelta.d];
    return verts.map((start, i) => {
      const end = verts[(i + 1) % verts.length];
      const c0 = deltaColor(deltas[i]);
      const c1 = deltaColor(deltas[(i + 1) % deltas.length]);
      const gradId = `vad-edge-${uid}-${i}`;
      return { start, end, c0, c1, gradId };
    });
  }, [compareCurrentVisualPoint, compareDelta, cx, cy, maxR, uid]);

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      role="img"
      aria-hidden={!showLabels}
    >
      <defs>
        {compareEdges?.map((edge) => (
          <linearGradient
            key={edge.gradId}
            id={edge.gradId}
            gradientUnits="userSpaceOnUse"
            x1={edge.start[0]}
            y1={edge.start[1]}
            x2={edge.end[0]}
            y2={edge.end[1]}
          >
            <stop offset="0%" stopColor={edge.c0} />
            <stop offset="100%" stopColor={edge.c1} />
          </linearGradient>
        ))}
      </defs>

      {gridPaths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="currentColor" strokeOpacity={0.12} strokeWidth={1} />
      ))}
      {axisLines.map((line, i) => (
        <line
          key={i}
          x1={line.x1}
          y1={line.y1}
          x2={line.x2}
          y2={line.y2}
          stroke="currentColor"
          strokeOpacity={0.15}
          strokeWidth={1}
        />
      ))}

      {layers.map((layer, layerIndex) => {
        const pointForDraw =
          compareEdges && layerIndex === 1 && compareCurrentVisualPoint
            ? compareCurrentVisualPoint
            : layer.point;
        const verts = vadVertices(pointForDraw, cx, cy, maxR);
        const path = polygonPathFromVertices(verts);
        const isCompareCurrent = compareEdges && layerIndex === 1;
        const isComparePrev = comparePrev && layerIndex === 0;

        if (isCompareCurrent) {
          return (
            <g key={layerIndex}>
              <path
                d={path}
                fill={layer.fill}
                fillOpacity={layer.fillOpacity ?? 0.18}
                stroke="none"
              />
              {compareEdges.map((edge, ei) => (
                <line
                  key={ei}
                  x1={edge.start[0]}
                  y1={edge.start[1]}
                  x2={edge.end[0]}
                  y2={edge.end[1]}
                  stroke={`url(#${edge.gradId})`}
                  strokeWidth={layer.strokeWidth ?? 2}
                  strokeLinecap="round"
                />
              ))}
            </g>
          );
        }

        return (
          <path
            key={layerIndex}
            d={path}
            fill={layer.fill}
            fillOpacity={layer.fillOpacity ?? (isComparePrev ? 0.12 : 0.2)}
            stroke={layer.stroke}
            strokeWidth={layer.strokeWidth ?? (isComparePrev ? 1.5 : 2)}
            strokeOpacity={isComparePrev ? 0.55 : 0.9}
          />
        );
      })}

      {showLabels
        ? labelPositions.map(({ label, x, y }) => (
            <text
              key={label}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-muted-foreground text-[9px]"
            >
              {label}
            </text>
          ))
        : null}
    </svg>
  );
}
