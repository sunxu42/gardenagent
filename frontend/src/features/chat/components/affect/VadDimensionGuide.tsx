import { VAD_DIMENSIONS } from "../../lib/vadDimensions";

function VadAxisScale({
  bipolar,
  poleLow,
  poleHigh,
  min,
  max,
}: {
  bipolar: boolean;
  poleLow: string;
  poleHigh: string;
  min: number;
  max: number;
}) {
  const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));

  if (bipolar) {
    return (
      <div className="mt-2.5" role="img" aria-label={`${poleLow} 至 ${poleHigh} 双向量表`}>
        <div className="flex items-center justify-between text-[10px] text-muted-foreground">
          <span>{poleLow}</span>
          <span className="text-muted-foreground/70">中性</span>
          <span className="text-primary">{poleHigh}</span>
        </div>
        <div className="relative mt-1 h-2 overflow-hidden rounded-full bg-muted/40">
          <div
            className="absolute inset-0 bg-gradient-to-r from-slate-400/75 via-slate-300/45 to-primary"
            aria-hidden
          />
        </div>
        <div className="mt-0.5 flex items-center justify-between text-[9px] tabular-nums text-muted-foreground">
          <span>{fmt(min)}</span>
          <span>0</span>
          <span>{fmt(max)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-2.5" role="img" aria-label={`${poleLow} 至 ${poleHigh} 单向量表`}>
      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{poleLow}</span>
        <span className="text-primary">{poleHigh}</span>
      </div>
      <div className="relative mt-1 h-2 overflow-hidden rounded-full bg-muted/40">
        <div
          className="absolute inset-0 bg-gradient-to-r from-primary/30 to-primary"
          aria-hidden
        />
      </div>
      <div className="mt-0.5 flex items-center justify-between text-[9px] tabular-nums text-muted-foreground">
        <span>{fmt(min)}</span>
        <span>{fmt(max)}</span>
      </div>
    </div>
  );
}

function formatRange(min: number, max: number): string {
  const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  return `${fmt(min)} ~ ${fmt(max)}`;
}

/** 三维度说明（用于右侧引导栏）— 文字为主，辅以轴端标签示意 */
export function VadDimensionGuide() {
  return (
    <div className="space-y-2">
      {VAD_DIMENSIONS.map((dim) => (
        <article
          key={dim.key}
          className="rounded-md bg-muted/20 px-3 py-2.5"
        >
          <header className="flex items-start gap-2.5">
            <span
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/12 text-xs font-semibold text-primary"
              aria-hidden
            >
              {dim.shortLabel}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0">
                <h5 className="text-xs font-medium text-foreground">{dim.fullName}</h5>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                {dim.description}
              </p>
            </div>
          </header>

          <VadAxisScale
            bipolar={dim.bipolar}
            poleLow={dim.poleLow}
            poleHigh={dim.poleHigh}
            min={dim.min}
            max={dim.max}
          />

          <p className="mt-2 text-[10px] text-muted-foreground/80">
            取值范围 {formatRange(dim.min, dim.max)}
          </p>
        </article>
      ))}
    </div>
  );
}
