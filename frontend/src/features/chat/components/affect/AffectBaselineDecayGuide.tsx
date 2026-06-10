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
  const { perTurnAlpha: agentAlpha, perTurnBeta: agentBeta, timeTauSec: agentTauSec } = p.agentVad;
  const { perTurnAlpha: relAlpha, timeTauSec: relTauSec } = p.relationship;
  const agentTau = formatTauLabel(agentTauSec);
  const relTau = formatTauLabel(relTauSec);

  return (
    <div className="space-y-3">
      <p className="text-[11px] leading-relaxed text-muted-foreground">
        助手 VAD 与关系持久化并各有 baseline：每轮对话走 appraisal 更新，长时间无对话则按 τ 向 baseline 回落。用户情绪每轮单独评估，不参与此状态机。
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
          detail="每轮：appraisal 产出当轮 user VAD，只注入本轮上下文。"
          note="无持久化、无 baseline、无每轮/闲置衰减。"
        />
        <GuideModuleCard
          accent="sky"
          label="助手 VAD"
          detail={`每轮：先向 synthesis 目标靠拢（强度 α×权重，α=${agentAlpha}），再向 VAD baseline 回拉（β=${agentBeta}）。`}
          note={`闲置：V/A/D 各维向 baseline 插值，步长 1−e^(−Δt/τ)，τ=${agentTau}（${agentTauSec}s）。Δt 为距上次更新的秒数。`}
        />
        <GuideModuleCard
          accent="amber"
          label="关系"
          detail={`每轮：信任、亲近 += appraisal 的 Δ × α × 权重（α=${relAlpha}）；写入前先结算闲置衰减。`}
          note={`闲置：信任、亲近向关系 baseline 插值，步长 1−e^(−Δt/τ)，τ=${relTau}（${relTauSec}s）。`}
        />
      </div>
    </div>
  );
}
