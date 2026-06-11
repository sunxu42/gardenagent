import { useRef, useState } from "react";

import type {
  EmotionEvalRequest,
  EmotionEvalResponse,
  InitialMood,
} from "@/features/test/types";
import { runEmotionEval } from "@/services/eval/evalApi";

const DEFAULT_FORM: EmotionEvalRequest = {
  background: "独居，最近工作压力大，睡眠质量下降。",
  initial_mood: "anxious",
  rounds: 5,
  goal: "评估 agent 的情绪支持质量",
};

const MOOD_OPTIONS: Array<{ value: InitialMood; label: string }> = [
  { value: "anxious", label: "焦虑" },
  { value: "sad", label: "难过" },
  { value: "angry", label: "生气" },
  { value: "lonely", label: "孤独" },
  { value: "stressed", label: "压力大" },
  { value: "neutral", label: "平静" },
];

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function clampRounds(value: number): number {
  if (!Number.isFinite(value)) {
    return DEFAULT_FORM.rounds;
  }
  return Math.min(8, Math.max(1, Math.round(value)));
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "评测运行失败";
}

export function TestPanel(): JSX.Element {
  const [form, setForm] = useState<EmotionEvalRequest>(DEFAULT_FORM);
  const [isRunning, setIsRunning] = useState(false);
  const isRunningRef = useRef(false);
  const [result, setResult] = useState<EmotionEvalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const updateForm = <Key extends keyof EmotionEvalRequest>(
    key: Key,
    value: EmotionEvalRequest[Key],
  ): void => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const updateRounds = (value: number): void => {
    if (!Number.isFinite(value)) {
      return;
    }
    updateForm("rounds", clampRounds(value));
  };

  const handleRun = async (): Promise<void> => {
    if (isRunningRef.current) {
      return;
    }

    isRunningRef.current = true;
    const scenario = { ...form, rounds: clampRounds(form.rounds) };
    setForm(scenario);
    setIsRunning(true);
    setError(null);
    setResult(null);

    try {
      const response = await runEmotionEval(scenario);
      setResult(response);
    } catch (runError) {
      setError(getErrorMessage(runError));
    } finally {
      isRunningRef.current = false;
      setIsRunning(false);
    }
  };

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden text-[color:var(--foreground)]">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
      <div className="rounded-2xl bg-[color:var(--card)] p-4">
        <div className="mb-5">
          <p className="text-sm font-medium text-[color:var(--muted-foreground)]">Emotion Eval</p>
          <h2 className="mt-1 text-2xl font-semibold text-[color:var(--foreground)]">
            情绪支持测试
          </h2>
          <p className="mt-2 text-sm text-[color:var(--muted-foreground)]">
            配置模拟用户场景，运行一次 agent 情绪支持质量评测。
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <label className="flex flex-col gap-2 text-sm font-medium">
            用户背景
            <textarea
              className="min-h-32 rounded-xl border border-[color:var(--border)] bg-[color:var(--background)] px-4 py-3 text-sm font-normal outline-none transition-colors focus:border-[color:var(--ring)]"
              value={form.background}
              onChange={(event) => updateForm("background", event.target.value)}
            />
          </label>

          <div className="grid gap-4 rounded-xl border border-[color:var(--border)] p-4">
            <label className="flex flex-col gap-2 text-sm font-medium">
              初始心情
              <select
                className="rounded-lg border border-[color:var(--border)] bg-[color:var(--background)] px-3 py-2 text-sm font-normal outline-none transition-colors focus:border-[color:var(--ring)]"
                value={form.initial_mood}
                onChange={(event) => updateForm("initial_mood", event.target.value as InitialMood)}
              >
                {MOOD_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value}/{option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium">
              测试轮次
              <input
                className="rounded-lg border border-[color:var(--border)] bg-[color:var(--background)] px-3 py-2 text-sm font-normal outline-none transition-colors focus:border-[color:var(--ring)]"
                max={8}
                min={1}
                type="number"
                value={form.rounds}
                onChange={(event) => updateRounds(event.target.valueAsNumber)}
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium">
              测试目标
              <input
                className="rounded-lg border border-[color:var(--border)] bg-[color:var(--background)] px-3 py-2 text-sm font-normal outline-none transition-colors focus:border-[color:var(--ring)]"
                value={form.goal}
                onChange={(event) => updateForm("goal", event.target.value)}
              />
            </label>

            <button
              className="cursor-pointer rounded-lg bg-[color:var(--primary)] px-4 py-2.5 text-sm font-semibold text-[color:var(--primary-foreground)] transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isRunning}
              type="button"
              onClick={handleRun}
            >
              {isRunning ? "测试中..." : "开始测试"}
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-[color:var(--destructive)] p-5 text-sm text-[color:var(--destructive)]">
          <p className="font-semibold">测试失败</p>
          <p className="mt-2">{error}</p>
        </div>
      ) : null}

      {result?.summary ? (
        <div className="rounded-2xl bg-[color:var(--muted)] p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-[color:var(--muted-foreground)]">总分</p>
              <p className="text-3xl font-semibold">{formatScore(result.summary.overall_score)}</p>
            </div>
            <span className="rounded-full border border-[color:var(--border)] px-3 py-1 text-sm font-medium">
              {result.summary.verdict}
            </span>
          </div>
          <p className="mt-4 text-sm leading-6">{result.summary.conclusion}</p>

          {result.summary.improvement_suggestions.length > 0 ? (
            <div className="mt-5">
              <p className="text-sm font-semibold">改进建议</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[color:var(--muted-foreground)]">
                {result.summary.improvement_suggestions.map((suggestion) => (
                  <li key={suggestion}>{suggestion}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {result ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">指标评分</h3>
            {result.scores.map((metric) => (
              <article
                className="rounded-2xl border border-[color:var(--border)] p-5"
                key={metric.name}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{metric.name}</p>
                  <p className="text-sm font-semibold text-[color:var(--primary)]">
                    {formatScore(metric.score)}
                  </p>
                </div>
                <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">
                  {metric.reason}
                </p>
              </article>
            ))}
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-semibold">对话轮次</h3>
            {result.turns.map((turn) => (
              <article
                className="rounded-2xl border border-[color:var(--border)] p-5"
                key={turn.round}
              >
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold">第 {turn.round} 轮</p>
                  {turn.agent_affect?.emotion ? (
                    <span className="rounded-full bg-[color:var(--accent)] px-3 py-1 text-xs font-medium text-[color:var(--accent-foreground)]">
                      {turn.agent_affect.emotion}
                    </span>
                  ) : null}
                </div>
                <div className="space-y-3 text-sm leading-6">
                  <p>
                    <span className="font-semibold">用户：</span>
                    {turn.user}
                  </p>
                  <p>
                    <span className="font-semibold">Agent：</span>
                    {turn.assistant}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
      </div>
    </section>
  );
}
