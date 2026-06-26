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
  latency_ms?: number | null;
  raw_updates?: string[];
}

export interface RunEnvironmentDTO {
  git_commit?: string | null;
  git_dirty?: boolean | null;
  agent_model?: string | null;
  eval_judge_model?: string | null;
  prompt_manifest_hash?: string | null;
  python_version?: string | null;
}

export interface RunTelemetryDTO {
  agent_cold_start?: boolean | null;
  agent_reused?: boolean | null;
  phase_durations_ms?: Record<string, number>;
  totals?: Record<string, number>;
}

export interface PersistedEventDTO {
  type: string;
  at: string;
  payload?: Record<string, unknown>;
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

export interface ScenarioSummary {
  id: string;
  description: string;
  domain: string;
  tier: "smoke" | "judge" | "exploratory";
  tags?: string[];
}

export interface CoverageScenarioRef {
  id: string;
  description: string;
  tags: string[];
  last_status: string | null;
  last_passed: boolean | null;
}

export interface CoverageCell {
  domain: string;
  domain_label: string;
  tier: "smoke" | "judge";
  scenario_count: number;
  scenarios: CoverageScenarioRef[];
  tags_covered: string[];
  tags_expected: string[];
  tags_missing: string[];
  last_run_at: string | null;
  pass_count: number;
  fail_count: number;
  pass_rate: number | null;
}

export interface CoverageMatrix {
  generated_at: string;
  cells: CoverageCell[];
  tag_coverage: Array<{
    tag: string;
    scenario_count: number;
    domains: string[];
  }>;
}

export interface AssertionResultDTO {
  name: string;
  status: "pass" | "fail" | "skip" | "warn";
  message: string;
}

export interface JudgeMetricScoreDTO {
  name: string;
  score: number;
  passed: boolean;
  threshold: number;
  reason: string;
}

export interface EvalRunResponse {
  run_id: string;
  mode: "scenario" | "exploratory";
  tier: "smoke" | "judge" | "exploratory";
  status: "running" | "completed" | "failed" | "cancelled";
  scenario_id?: string | null;
  observations: EmotionTurnResult[];
  assertions: AssertionResultDTO[];
  judge: JudgeMetricScoreDTO[];
  judge_overall_passed?: boolean | null;
  scores: EmotionMetricScore[];
  summary?: EvalSummary | null;
  error?: EvalErrorPayload | null;
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
  environment?: RunEnvironmentDTO | null;
  telemetry?: RunTelemetryDTO | null;
  events?: PersistedEventDTO[];
  exploratory_config?: EmotionEvalRequest | null;
}

export interface EvalRunStartedResponse {
  run_id: string;
  scenario_id: string;
  tier: "smoke" | "judge" | "exploratory";
  status: "running";
}

export interface EvalRunSummary {
  run_id: string;
  scenario_id: string;
  tier: "smoke" | "judge" | "exploratory";
  mode?: "scenario" | "exploratory";
  status: "running" | "completed" | "failed" | "cancelled";
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
  assertions_passed?: boolean | null;
  judge_overall_passed?: boolean | null;
}

export type PanelTab = "overview" | "history";

export type PanelView = "radar" | { kind: "domain"; domainId: string };

export type DomainMode = "smoke" | "judge" | "exploratory";

export type HistoryTierFilter = "all" | "smoke" | "judge" | "exploratory";

export type HistoryDomainFilter = "all" | string;

export function isDomainPanelView(
  view: PanelView,
): view is { kind: "domain"; domainId: string } {
  return view !== "radar" && typeof view === "object";
}
