import { Play, Sparkles, Square } from "lucide-react";
import { useState } from "react";

import {
  DEFAULT_EXPLORATORY_FORM,
  MOOD_OPTIONS,
  clampRounds,
} from "@/features/test/evalFormConstants";
import type { EmotionEvalRequest, InitialMood } from "@/features/test/types";

interface EvalExploratoryPaneProps {
  running: boolean;
  onRun: (request: EmotionEvalRequest) => void;
  onCancel: () => void;
}

export function EvalExploratoryPane({
  running,
  onRun,
  onCancel,
}: EvalExploratoryPaneProps): JSX.Element {
  const [form, setForm] = useState<EmotionEvalRequest>(DEFAULT_EXPLORATORY_FORM);

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

  const handleRun = (): void => {
    const scenario = { ...form, rounds: clampRounds(form.rounds) };
    setForm(scenario);
    onRun(scenario);
  };

  return (
    <div className="eval-domain-pane eval-domain-pane--exploratory">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
        <p className="text-[11px] text-muted-foreground">配置模拟用户，评估情绪支持质量</p>
      </div>

      <div className="space-y-3">
        <label className="flex flex-col gap-1.5">
          <span className="text-[11px] font-medium text-muted-foreground">用户背景</span>
          <textarea
            className="min-h-28 rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] leading-relaxed text-foreground outline-none transition-colors duration-200 focus:border-border"
            disabled={running}
            value={form.background}
            onChange={(event) => updateForm("background", event.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-[11px] font-medium text-muted-foreground">初始心情</span>
          <select
            className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
            disabled={running}
            value={form.initial_mood}
            onChange={(event) => updateForm("initial_mood", event.target.value as InitialMood)}
          >
            {MOOD_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-2">
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] font-medium text-muted-foreground">测试轮次</span>
            <input
              className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
              disabled={running}
              max={8}
              min={1}
              type="number"
              value={form.rounds}
              onChange={(event) => {
                const raw = event.target.value;
                if (raw === "") {
                  return;
                }
                updateRounds(Number(raw));
              }}
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] font-medium text-muted-foreground">测试目标</span>
            <input
              className="rounded-md border border-border/50 bg-background/60 px-3 py-2 text-[11px] text-foreground outline-none transition-colors duration-200 focus:border-border"
              disabled={running}
              value={form.goal}
              onChange={(event) => updateForm("goal", event.target.value)}
            />
          </label>
        </div>

        <button
          className={`test-action-btn ${running ? "test-action-btn--cancel" : "test-action-btn--run"}`}
          type="button"
          onClick={running ? onCancel : handleRun}
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            {running ? (
              <Square className="h-3 w-3" aria-hidden />
            ) : (
              <Play className="h-3 w-3" aria-hidden />
            )}
            {running ? "取消测试" : "开始测试"}
          </span>
        </button>
      </div>
    </div>
  );
}
