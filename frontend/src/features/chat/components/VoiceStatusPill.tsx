import type { VoiceState } from "../types";
import { Badge } from "@/components/ui/badge";

interface VoiceStatusPillProps {
  state: VoiceState;
}

const labelMap: Record<VoiceState, string> = {
  idle: "待命中",
  listening: "聆听中",
  recognizing: "识别中",
  sending: "发送中",
  agentThinking: "思考中",
  speaking: "播报中",
};

export function VoiceStatusPill({ state }: VoiceStatusPillProps) {
  if (state === "idle") {
    return null;
  }

  return (
    <Badge
      className={`voice-status-pill--${state} mb-2 text-xs`}
      variant={state === "speaking" ? "secondary" : "outline"}
      role="status"
      aria-live="polite"
    >
      {labelMap[state]}
    </Badge>
  );
}
