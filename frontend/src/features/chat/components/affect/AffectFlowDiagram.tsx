import { useId } from "react";

/** 情绪管线示意 — 柔和分层配色 */
export function AffectFlowDiagram() {
  const uid = useId().replace(/:/g, "");
  const arrowId = `affect-arrow-${uid}`;

  return (
    <div className="rounded-lg border border-border/35 bg-muted/12 p-3 opacity-90">
      <svg
        viewBox="0 0 300 340"
        className="mx-auto w-full max-w-[18rem]"
        role="img"
        aria-label="情绪模块处理流程：用户说话经感知、关系、策略到助手语气落地"
      >
        <defs>
          <linearGradient id={`grad-input-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#c4b5fd" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.2" />
          </linearGradient>
          <linearGradient id={`grad-user-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.12" />
          </linearGradient>
          <linearGradient id={`grad-rel-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.12" />
          </linearGradient>
          <linearGradient id={`grad-policy-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id={`grad-agent-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id={`grad-done-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.12" />
          </linearGradient>
          <marker id={arrowId} markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 Z" fill="#94a3b8" />
          </marker>
        </defs>

        <FlowBox
          x={95}
          y={4}
          w={110}
          h={38}
          step="0"
          label="你说的话"
          fill={`url(#grad-input-${uid})`}
          stroke="#a78bfa"
          accent="#8b5cf6"
        />
        <FlowArrow x1={150} y1={42} x2={150} y2={54} marker={arrowId} />

        <FlowBox
          x={72}
          y={54}
          w={156}
          h={44}
          step="A"
          label="用户情绪感知"
          sub="愉悦 · 能量 · 掌控"
          fill={`url(#grad-user-${uid})`}
          stroke="#8b5cf6"
          accent="#7c3aed"
        />
        <FlowArrow x1={150} y1={98} x2={150} y2={110} marker={arrowId} />

        <FlowBox
          x={72}
          y={110}
          w={156}
          h={44}
          step="B"
          label="关系更新"
          sub="信任 · 亲近"
          fill={`url(#grad-rel-${uid})`}
          stroke="#f59e0b"
          accent="#d97706"
        />
        <FlowArrow x1={150} y1={154} x2={150} y2={166} marker={arrowId} />

        <FlowBox
          x={58}
          y={166}
          w={184}
          h={44}
          step="C"
          label="回应策略"
          sub="共情 · 立场 · 态度"
          fill={`url(#grad-policy-${uid})`}
          stroke="#38bdf8"
          accent="#0284c7"
        />
        <FlowArrow x1={150} y1={210} x2={150} y2={222} marker={arrowId} />

        <FlowBox
          x={68}
          y={222}
          w={164}
          h={40}
          step="→"
          label="合成目标语气"
          sub="Agent VAD 目标"
          fill={`url(#grad-agent-${uid})`}
          stroke="#6366f1"
          accent="#4f46e5"
        />
        <FlowArrow x1={150} y1={262} x2={150} y2={274} marker={arrowId} />

        <FlowBox
          x={68}
          y={274}
          w={164}
          h={40}
          step="✓"
          label="状态机落地"
          sub="Agent 当前语气"
          fill={`url(#grad-done-${uid})`}
          stroke="#34d399"
          accent="#059669"
        />
      </svg>
    </div>
  );
}

function FlowBox({
  x,
  y,
  w,
  h,
  step,
  label,
  sub,
  fill,
  stroke,
  accent,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  step: string;
  label: string;
  sub?: string;
  fill: string;
  stroke: string;
  accent: string;
}) {
  const textY = sub ? y + 18 : y + 22;
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={10} fill={fill} stroke={stroke} strokeWidth={1.2} opacity={0.95} />
      <rect x={x} y={y} width={4} height={h} rx={2} fill={accent} />
      <circle cx={x + 16} cy={y + h / 2} r={9} fill={accent} fillOpacity={0.15} stroke={accent} strokeWidth={1} />
      <text
        x={x + 16}
        y={y + h / 2 + (step.length > 1 ? 3 : 4)}
        textAnchor="middle"
        fill={accent}
        fontSize={step.length > 1 ? 8 : 10}
        fontWeight={600}
      >
        {step}
      </text>
      <text x={x + w / 2 + 6} y={textY} textAnchor="middle" fill="currentColor" className="text-foreground" fontSize={11} fontWeight={600}>
        {label}
      </text>
      {sub ? (
        <text x={x + w / 2 + 6} y={y + 32} textAnchor="middle" fill="#64748b" fontSize={9}>
          {sub}
        </text>
      ) : null}
    </g>
  );
}

function FlowArrow({
  x1,
  y1,
  x2,
  y2,
  marker,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  marker: string;
}) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke="#cbd5e1"
      strokeWidth={1.5}
      strokeDasharray="4 3"
      markerEnd={`url(#${marker})`}
    />
  );
}
