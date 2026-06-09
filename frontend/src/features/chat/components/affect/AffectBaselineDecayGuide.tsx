import type { EmotionProfile, VadPoint } from "../../types";
import { formatVadTriple } from "../../lib/affectFormat";
import { inferUserMood } from "../../lib/affectPresentation";
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

function BaselineRadarCard({
  side,
  label,
  point,
  stroke,
  fill,
  hint,
}: {
  side: "user" | "agent";
  label: string;
  point: VadPoint;
  stroke: string;
  fill: string;
  hint: string;
}) {
  const sideStyles =
    side === "user"
      ? "border-violet-200/60 bg-violet-50/30 dark:border-violet-500/20 dark:bg-violet-500/5"
      : "border-slate-200/70 bg-slate-50/40 dark:border-slate-500/25 dark:bg-slate-500/5";

  return (
    <div
      className={`flex min-w-0 flex-1 flex-col items-center rounded-lg border px-4 py-3.5 text-center ${sideStyles}`}
    >
      <p className="mb-1 text-[10px] font-semibold tracking-wide text-foreground">{label}</p>
      <p className="mb-3 max-w-[9rem] text-[10px] leading-relaxed text-muted-foreground">{hint}</p>
      <VadRadarChart
        size={76}
        showLabels
        className="text-border"
        layers={[
          {
            point,
            stroke,
            fill,
            fillOpacity: 0.16,
            strokeWidth: 1.8,
          },
        ]}
      />
      <p className="mt-3 font-mono text-[10px] leading-snug text-muted-foreground">{formatVadTriple(point)}</p>
    </div>
  );
}

export function AffectBaselineDecayGuide({
  profile,
  agentBaselineFallback,
}: AffectBaselineDecayGuideProps) {
  const p = resolveEmotionProfile(profile, agentBaselineFallback);
  const userMood = inferUserMood(p.userVadBaseline);
  const { trust, warmth } = p.relationshipBaseline;
  const agentTau = formatTauLabel(p.agentVad.timeTauSec);
  const relTau = formatTauLabel(p.relationship.timeTauSec);

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border/30 bg-muted/12 p-3.5">
        <p className="mb-3 text-[11px] leading-relaxed text-muted-foreground">
          Baseline 是「回到默认」时的参考点。助手与关系会持久化并随时间向 baseline 回落；用户侧每轮重新感知。
        </p>
        <div className="grid gap-3 sm:grid-cols-2 sm:gap-4">
          <BaselineRadarCard
            side="user"
            label="用户 baseline"
            hint={`中性参考 · ${userMood.label}`}
            point={p.userVadBaseline}
            stroke="#8b5cf6"
            fill="#8b5cf6"
          />
          <BaselineRadarCard
            side="agent"
            label="助手 baseline"
            hint="人格基线 · 来自角色设定"
            point={p.agentVadBaseline}
            stroke="#64748b"
            fill="#64748b"
          />
        </div>
        <p className="mt-4 border-t border-border/25 pt-3 text-center text-[11px] text-muted-foreground">
          关系 baseline：信任 {formatPercent01(trust)} / 亲近 {formatPercent01(warmth)}
        </p>
      </div>

      <div className="space-y-2">
        <GuideModuleCard
          accent="violet"
          label="用户情绪"
          detail={`每轮重新估计；展示值经 EMA（α=${p.userAffect.emaAlpha}）短窗平滑，不随闲置时间回落。`}
        />
        <GuideModuleCard
          accent="sky"
          label="助手语气"
          detail={`每轮朝目标靠拢（α=${p.agentVad.perTurnAlpha}×权重）后轻拉 baseline（β=${p.agentVad.perTurnBeta}）；闲置 τ=${agentTau} 指数回归。`}
        />
        <GuideModuleCard
          accent="amber"
          label="关系"
          detail={`小步 Δ + α=${p.relationship.perTurnAlpha} 融入；闲置向 baseline 回归，τ=${relTau}。`}
        />
      </div>

      <details className="rounded-md border border-border/30 bg-muted/8 text-[11px] text-muted-foreground">
        <summary className="cursor-pointer px-3 py-2 transition-colors duration-200 hover:bg-muted/20">
          衰减公式（进阶）
        </summary>
        <p className="border-t border-border/25 px-3 py-2 leading-relaxed">
          靠拢比例 = 1 − e^(−Δt/τ)。Δt 越大越接近 baseline；τ 越大回落越慢、惯性越强。
        </p>
      </details>
    </div>
  );
}
