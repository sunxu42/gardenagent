import type {
  AgentAffectSnapshot,
  AssertionResultDTO,
  EmotionMetricScore,
  EvalSummary,
  JudgeMetricScoreDTO,
} from "@/features/test/types";

export type EvalWsEventType =
  | "eval_started"
  | "eval_progress"
  | "eval_turn"
  | "eval_assertions"
  | "eval_judge_metric"
  | "eval_completed"
  | "eval_failed"
  | "eval_cancelled";

export interface EvalWsEvent {
  type: EvalWsEventType;
  run_id: string;
  scenario_id?: string;
  tier?: string;
  description?: string;
  phase?: string;
  message?: string;
  round?: number;
  total_rounds?: number;
  judge_index?: number;
  judge_total?: number;
  metric_name?: string;
  reused_agent?: boolean;
  user?: string;
  assistant?: string;
  agent_affect?: AgentAffectSnapshot | null;
  assertions?: AssertionResultDTO[];
  name?: string;
  score?: number;
  passed?: boolean;
  threshold?: number;
  reason?: string;
  status?: string;
  judge_overall_passed?: boolean | null;
  scores?: EmotionMetricScore[];
  summary?: EvalSummary | null;
  error?: { code: string; message: string };
}
