import { Play, Sparkles, Square } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  DEFAULT_EXPLORATORY_FORM,
  MOOD_OPTIONS,
  clampRounds,
} from "@/features/test/evalFormConstants";
import type { EmotionEvalRequest, InitialMood } from "@/features/test/types";
import { cn } from "@/lib/utils";

interface EvalExploratoryPaneProps {
  running: boolean;
  onRun: (request: EmotionEvalRequest) => void;
  onCancel: () => void;
}

const fieldClassName =
  "border-border/50 bg-background/60 text-[11px] transition-colors duration-200 focus-visible:border-border";

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
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="exploratory-background" className="text-[11px] text-muted-foreground">
            用户背景
          </Label>
          <Textarea
            id="exploratory-background"
            className={cn("min-h-28 leading-relaxed", fieldClassName)}
            disabled={running}
            value={form.background}
            onChange={(event) => updateForm("background", event.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="exploratory-mood" className="text-[11px] text-muted-foreground">
            初始心情
          </Label>
          <Select
            disabled={running}
            value={form.initial_mood}
            onValueChange={(value) => updateForm("initial_mood", value as InitialMood)}
          >
            <SelectTrigger id="exploratory-mood" className={cn("h-9", fieldClassName)}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MOOD_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value} className="text-[11px]">
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="exploratory-rounds" className="text-[11px] text-muted-foreground">
              测试轮次
            </Label>
            <Input
              id="exploratory-rounds"
              className={cn("h-9", fieldClassName)}
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
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="exploratory-goal" className="text-[11px] text-muted-foreground">
              测试目标
            </Label>
            <Input
              id="exploratory-goal"
              className={cn("h-9", fieldClassName)}
              disabled={running}
              value={form.goal}
              onChange={(event) => updateForm("goal", event.target.value)}
            />
          </div>
        </div>

        <Button
          type="button"
          variant={running ? "secondary" : "default"}
          className={cn(
            "test-action-btn h-auto w-full",
            running ? "test-action-btn--cancel" : "test-action-btn--run",
          )}
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
        </Button>
      </div>
    </div>
  );
}
