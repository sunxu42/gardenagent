export type InitialMood = "anxious" | "sad" | "angry" | "lonely" | "stressed" | "neutral";

export interface EmotionEvalRequest {
  background: string;
  initial_mood: InitialMood;
  rounds: number;
  goal: string;
}

export interface AgentAffectSnapshot {
  emotion?: string | null;
  vad?: { v: number; a: number; d: number } | null;
  relationship_stage?: string | null;
}

export interface EmotionTurnResult {
  round: number;
  user: string;
  assistant: string;
  agent_affect?: AgentAffectSnapshot | null;
}

export interface EmotionMetricScore {
  name: string;
  score: number;
  reason: string;
  evidence: string[];
}

export interface EvalSummary {
  overall_score: number;
  verdict: "pass" | "warning" | "fail";
  conclusion: string;
  improvement_suggestions: string[];
}

export interface EvalErrorPayload {
  code: string;
  message: string;
}

export interface EmotionEvalResponse {
  session_id: string;
  status: "completed" | "failed";
  scenario?: EmotionEvalRequest | null;
  turns: EmotionTurnResult[];
  scores: EmotionMetricScore[];
  summary?: EvalSummary | null;
  error?: EvalErrorPayload | null;
}
