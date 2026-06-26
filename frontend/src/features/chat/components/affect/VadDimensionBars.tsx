import type { VadPoint } from "../../types";
import {
  VAD_DIMENSIONS,
  formatVadValue,
  vadDimensionVerbal,
  vadValueToPercent,
  type VadDimensionMeta,
} from "../../lib/vadDimensions";

interface VadDimensionBarsProps {
  point: VadPoint;
  compare?: VadPoint | null;
  compact?: boolean;
}

function BipolarBar({ dim, value }: { dim: VadDimensionMeta; value: number }) {
  const pct = vadValueToPercent(value, dim);
  const isRight = value >= 0;
  const width = dim.bipolar ? Math.abs(value) * 50 : pct;

  return (
    <div className="relative h-2 overflow-hidden rounded-full bg-muted">
      <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-border/80" aria-hidden />
      <div
        className={`absolute top-0 h-full rounded-full transition-[width] duration-300 ease-out motion-reduce:transition-none ${
          isRight ? "left-1/2 bg-violet-500/75" : "right-1/2 bg-violet-500/75"
        }`}
        style={{ width: `${Math.min(50, width)}%` }}
      />
    </div>
  );
}

function UnipolarBar({ dim, value }: { dim: VadDimensionMeta; value: number }) {
  const pct = vadValueToPercent(value, dim);
  return (
    <div className="h-2 overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full bg-primary/70 transition-[width] duration-300 ease-out motion-reduce:transition-none"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function VadDimensionBars({ point, compare, compact }: VadDimensionBarsProps) {
  return (
    <div className={compact ? "space-y-2" : "space-y-3"}>
      {VAD_DIMENSIONS.map((dim) => {
        const value = point[dim.key];
        const compareVal = compare?.[dim.key];
        return (
          <div key={dim.key}>
            <div className="mb-1 flex items-baseline justify-between gap-2 text-xs">
              <span className="font-medium text-foreground">
                {dim.shortLabel}
                <span className="ml-1.5 font-normal text-muted-foreground">{dim.hint}</span>
              </span>
              <span className="shrink-0 tabular-nums text-muted-foreground">
                {formatVadValue(value, dim)}
                <span className="ml-1 text-[10px]">({vadDimensionVerbal(dim.key, value)})</span>
              </span>
            </div>
            {dim.bipolar ? (
              <BipolarBar dim={dim} value={value} />
            ) : (
              <UnipolarBar dim={dim} value={value} />
            )}
            {compareVal != null && Math.abs(compareVal - value) > 0.02 ? (
              <p className="mt-0.5 text-[10px] text-muted-foreground">
                较上轮 {value > compareVal ? "↑" : "↓"} {formatVadValue(Math.abs(value - compareVal), dim)}
              </p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
