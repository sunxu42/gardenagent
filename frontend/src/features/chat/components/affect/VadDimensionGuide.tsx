import { VAD_DIMENSIONS, vadValueToPercent } from "../../lib/vadDimensions";

/** 三维度说明条（用于右侧引导栏） */
export function VadDimensionGuide() {
  return (
    <div className="space-y-3">
      {VAD_DIMENSIONS.map((dim) => (
        <div key={dim.key}>
          <div className="mb-1 flex items-baseline justify-between gap-2">
            <span className="text-xs font-medium text-foreground">{dim.label}</span>
            <span className="text-[10px] text-muted-foreground">{dim.hint}</span>
          </div>
          <div className="relative h-2.5 overflow-hidden rounded-full bg-muted/80">
            {dim.bipolar ? (
              <>
                <div className="absolute left-1/2 top-0 h-full w-px bg-border/80" />
                <div
                  className="absolute top-0 h-full rounded-r-full bg-muted-foreground/25"
                  style={{
                    left: "50%",
                    width: `${vadValueToPercent(0.55, dim) / 2}%`,
                  }}
                />
                <div
                  className="absolute top-0 h-full rounded-l-full bg-muted-foreground/18"
                  style={{
                    right: "50%",
                    width: `${vadValueToPercent(0.55, dim) / 2}%`,
                  }}
                />
              </>
            ) : (
              <div
                className="h-full rounded-full bg-muted-foreground/22"
                style={{ width: `${vadValueToPercent(0.55, dim)}%` }}
              />
            )}
          </div>
          <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground">
            {dim.key === "v" && "衡量积极/消极感受，影响对你情绪的判断。"}
            {dim.key === "a" && "衡量激动/平静程度，高能量常对应紧张或兴奋。"}
            {dim.key === "d" && "衡量强势/被动感受，影响语气是坚定还是退让。"}
          </p>
        </div>
      ))}
    </div>
  );
}
