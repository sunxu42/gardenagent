import type { EmotionProfile, VadPoint } from "../../types";
import { formatVadTriple } from "../../lib/affectFormat";
import {
  formatPercent01,
  formatTauLabel,
  resolveEmotionProfile,
} from "../../lib/emotionProfile";
import { VadRadarChart } from "../VadRadarChart";
import { GuideModuleCard } from "./GuideSection";

interface AffectBaselineDecayGuideProps {
  profile?: EmotionProfile | null;
  agentBaselineFallback?: VadPoint | null;
}

export function AffectBaselineDecayGuide({
  profile,
  agentBaselineFallback,
}: AffectBaselineDecayGuideProps) {
  const p = resolveEmotionProfile(profile, agentBaselineFallback);
  const { trust, warmth } = p.relationshipBaseline;
  const agentTau = formatTauLabel(p.agentVad.timeTauSec);
  const relTau = formatTauLabel(p.relationship.timeTauSec);

  return (
    <div className="space-y-3">
      <p className="text-[11px] leading-relaxed text-muted-foreground">
        仅助手 VAD 与关系有 baseline 并随闲置回落；用户情绪每轮重评，无 baseline。
      </p>

      <div className="flex flex-col items-center rounded-md border border-border/30 bg-muted/20 px-4 py-3.5 text-center">
        <p className="text-[10px] font-medium text-foreground">助手 VAD baseline</p>
        <VadRadarChart
          size={84}
          showLabels
          className="mt-2 text-border"
          layers={[
            {
              point: p.agentVadBaseline,
              stroke: "#64748b",
              fill: "#64748b",
              fillOpacity: 0.16,
              strokeWidth: 1.8,
            },
          ]}
        />
        <p className="mt-2 font-mono text-[10px] text-muted-foreground">
          {formatVadTriple(p.agentVadBaseline)}
        </p>
        <p className="mt-3 text-[11px] text-muted-foreground">
          关系 baseline：信任 {formatPercent01(trust)} · 亲近 {formatPercent01(warmth)}
        </p>
      </div>

      <div className="space-y-1.5">
        <GuideModuleCard
          accent="violet"
          label="用户"
          detail="每轮评估，不持久化，不衰减。"
        />
        <GuideModuleCard
          accent="sky"
          label="助手 VAD"
          detail={`靠拢 α=${p.agentVad.perTurnAlpha}，回拉 β=${p.agentVad.perTurnBeta}，τ=${agentTau}`}
        />
        <GuideModuleCard
          accent="amber"
          label="关系"
          detail={`Δ 融入 α=${p.relationship.perTurnAlpha}，τ=${relTau}`}
        />
      </div>

      <details className="rounded-md bg-muted/20 text-[11px] text-muted-foreground">
        <summary className="cursor-pointer px-3 py-2 transition-colors duration-200 hover:bg-muted/30">
          衰减公式
        </summary>
        <p className="px-3 pb-2 leading-relaxed">
          1 − e^(−Δt/τ)：Δt 越大越接近 baseline，τ 越大回落越慢。
        </p>
      </details>
    </div>
  );
}
