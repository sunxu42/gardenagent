import type { EvalRunResponse } from "@/features/test/types";
import { formatDurationZh, labelEvalPhase } from "@/lib/uiLabels";

function formatTelemetryDuration(durationMs: number | null | undefined): string {
  if (durationMs === null || durationMs === undefined) {
    return "—";
  }
  return formatDurationZh(durationMs);
}

function hasTelemetryData(result: Partial<EvalRunResponse>): boolean {
  return Boolean(
    result.duration_ms ||
      result.environment?.git_commit ||
      result.environment?.agent_model ||
      result.telemetry?.agent_cold_start !== undefined,
  );
}

interface EvalRunTelemetryViewProps {
  result: Partial<EvalRunResponse>;
}

export function EvalRunTelemetryView({ result }: EvalRunTelemetryViewProps): JSX.Element {
  if (!hasTelemetryData(result)) {
    return (
      <section className="test-panel-section">
        <p className="text-[11px] text-muted-foreground">无遥测数据（旧版记录）</p>
      </section>
    );
  }

  const env = result.environment;
  const telemetry = result.telemetry;

  return (
    <section className="test-panel-section">
      <h4 className="test-panel-section__title">运行遥测</h4>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-[11px]">
        <div>
          <dt className="text-muted-foreground">总耗时</dt>
          <dd className="font-medium text-foreground">{formatTelemetryDuration(result.duration_ms)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">助手冷启动</dt>
          <dd className="font-medium text-foreground">
            {telemetry?.agent_cold_start === true
              ? "是"
              : telemetry?.agent_cold_start === false
                ? "否"
                : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">助手模型</dt>
          <dd className="truncate font-medium text-foreground">{env?.agent_model ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">评判模型</dt>
          <dd className="truncate font-medium text-foreground">{env?.eval_judge_model ?? "—"}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-muted-foreground">代码提交</dt>
          <dd className="font-mono text-[10px] text-foreground">{env?.git_commit ?? "—"}</dd>
        </div>
      </dl>
      {telemetry?.phase_durations_ms && Object.keys(telemetry.phase_durations_ms).length > 0 ? (
        <div className="mt-3 border-t border-border/25 pt-2">
          <p className="mb-1.5 text-[10px] font-medium text-muted-foreground">阶段耗时</p>
          <ul className="flex flex-wrap gap-2">
            {Object.entries(telemetry.phase_durations_ms).map(([phase, ms]) => (
              <li className="test-panel-card text-[10px]" key={phase}>
                {labelEvalPhase(phase)} · {formatTelemetryDuration(ms)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
