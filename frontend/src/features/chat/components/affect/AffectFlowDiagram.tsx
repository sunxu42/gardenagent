import { useId } from "react";

interface PipelineStep {
  step: string;
  label: string;
  sub: string;
  layer: "client" | "transport" | "handler" | "emotion" | "llm" | "tts";
}

/** 全链路节点；展示时仅保留业务主路径并重新编号 */
const PIPELINE_SOURCE: PipelineStep[] = [
  { step: "1", label: "客户端输入", sub: "文字发送 / 语音 ASR", layer: "client" },
  { step: "2", label: "WebSocket", sub: "消息到达 Handler", layer: "transport" },
  { step: "3", label: "Handler 入队", sub: "登记 turn_id · 等待评估", layer: "handler" },
  { step: "4", label: "情绪评估 LLM", sub: "用户 V/A/D · 关系 Δ", layer: "emotion" },
  { step: "5", label: "策略合成", sub: "共情 · 目标语气 · 标签", layer: "emotion" },
  { step: "6", label: "状态机写入", sub: "Agent VAD · 关系持久化", layer: "emotion" },
  { step: "7", label: "推送 appraised", sub: "affect_turn_appraised", layer: "transport" },
  { step: "8", label: "Prompt 注入", sub: "情感上下文 · 策略模块", layer: "llm" },
  { step: "9", label: "主 LLM 生成", sub: "流式文本回复", layer: "llm" },
  { step: "10", label: "TTS 合成", sub: "情感 · 语速 · 音调", layer: "tts" },
  { step: "11", label: "推送 settled", sub: "affect_turn_settled + 音频", layer: "transport" },
  { step: "12", label: "客户端展示", sub: "情绪记录 · 播放回复", layer: "client" },
];

const VISIBLE_STEP_IDS = ["1", "4", "5", "8", "9", "10", "12"] as const;

const PIPELINE: PipelineStep[] = VISIBLE_STEP_IDS.flatMap((id, index) => {
  const item = PIPELINE_SOURCE.find((s) => s.step === id);
  return item ? [{ ...item, step: String(index + 1) }] : [];
});

const LAYER_STYLE: Record<
  PipelineStep["layer"],
  { stroke: string; accent: string; gradA: string; gradB: string }
> = {
  client: { stroke: "#a78bfa", accent: "#8b5cf6", gradA: "#c4b5fd", gradB: "#a78bfa" },
  transport: { stroke: "#94a3b8", accent: "#64748b", gradA: "#cbd5e1", gradB: "#94a3b8" },
  handler: { stroke: "#38bdf8", accent: "#0284c7", gradA: "#38bdf8", gradB: "#0ea5e9" },
  emotion: { stroke: "#f59e0b", accent: "#d97706", gradA: "#fbbf24", gradB: "#f59e0b" },
  llm: { stroke: "#6366f1", accent: "#4f46e5", gradA: "#818cf8", gradB: "#6366f1" },
  tts: { stroke: "#34d399", accent: "#059669", gradA: "#34d399", gradB: "#10b981" },
};

const BOX_W = 196;
const BOX_H = 40;
const BOX_X = 52;
const GAP = 8;
const TOP = 8;

/** 全链路纵向流程：客户端 → 服务端 → 大模型 → 回复 */
export function AffectFlowDiagram() {
  const uid = useId().replace(/:/g, "");
  const arrowId = `pipeline-arrow-${uid}`;
  const totalH = TOP + PIPELINE.length * (BOX_H + GAP) - GAP + 12;
  const viewH = totalH + 16;

  return (
    <div className="rounded-md bg-muted/15 py-2">
      <svg
        viewBox={`0 0 300 ${viewH}`}
        className="mx-auto w-full max-w-[20rem]"
        role="img"
        aria-label="对话主链路：输入、情绪评估与合成、生成回复、TTS 与展示"
      >
        <defs>
          {Object.entries(LAYER_STYLE).map(([layer, s]) => (
            <linearGradient key={layer} id={`grad-${layer}-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={s.gradA} stopOpacity="0.28" />
              <stop offset="100%" stopColor={s.gradB} stopOpacity="0.1" />
            </linearGradient>
          ))}
          <marker id={arrowId} markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 Z" fill="#94a3b8" />
          </marker>
        </defs>

        {PIPELINE.map((item, i) => {
          const y = TOP + i * (BOX_H + GAP);
          const style = LAYER_STYLE[item.layer];
          const cx = BOX_X + BOX_W / 2;
          return (
            <g key={`${item.label}-${i}`}>
              {i > 0 ? (
                <line
                  x1={cx}
                  y1={y - GAP}
                  x2={cx}
                  y2={y}
                  stroke="#cbd5e1"
                  strokeWidth={1.5}
                  strokeDasharray="4 3"
                  markerEnd={`url(#${arrowId})`}
                />
              ) : null}
              <FlowBox
                x={BOX_X}
                y={y}
                w={BOX_W}
                h={BOX_H}
                step={item.step}
                label={item.label}
                sub={item.sub}
                fill={`url(#grad-${item.layer}-${uid})`}
                stroke={style.stroke}
                accent={style.accent}
              />
            </g>
          );
        })}
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
  sub: string;
  fill: string;
  stroke: string;
  accent: string;
}) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={9} fill={fill} stroke={stroke} strokeWidth={1.1} opacity={0.95} />
      <rect x={x} y={y} width={4} height={h} rx={2} fill={accent} />
      <circle cx={x + 15} cy={y + h / 2} r={8} fill={accent} fillOpacity={0.15} stroke={accent} strokeWidth={1} />
      <text
        x={x + 15}
        y={y + h / 2 + 3}
        textAnchor="middle"
        fill={accent}
        fontSize={9}
        fontWeight={600}
      >
        {step}
      </text>
      <text
        x={x + w / 2 + 8}
        y={y + 16}
        textAnchor="middle"
        fill="currentColor"
        className="text-foreground"
        fontSize={10}
        fontWeight={600}
      >
        {label}
      </text>
      <text x={x + w / 2 + 8} y={y + 30} textAnchor="middle" fill="#64748b" fontSize={8.5}>
        {sub}
      </text>
    </g>
  );
}
