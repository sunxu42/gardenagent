import type {
  EvalRunResponse,
  EvalRunStartedResponse,
  EvalRunSummary,
  ScenarioSummary,
} from "@/features/test/types";

export async function listScenarios(
  tier?: "smoke" | "judge",
  signal?: AbortSignal,
): Promise<ScenarioSummary[]> {
  const query = tier ? `?tier=${tier}` : "";
  const response = await fetch(`/api/eval/scenarios${query}`, { signal });
  if (!response.ok) {
    throw new Error("加载场景列表失败");
  }
  return (await response.json()) as ScenarioSummary[];
}

export async function runScenarioEval(scenarioId: string): Promise<EvalRunResponse> {
  const response = await fetch("/api/eval/scenario/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId, persist: true }),
  });
  const payload = (await response.json()) as EvalRunResponse;
  if (!response.ok || payload.status === "failed") {
    throw new Error(payload.error?.message || "场景评测运行失败");
  }
  return payload;
}

export async function startScenarioEvalAsync(
  scenarioId: string,
  clientId: string,
): Promise<EvalRunStartedResponse> {
  const response = await fetch("/api/eval/scenario/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_id: scenarioId,
      client_id: clientId,
      async: true,
      persist: true,
    }),
  });
  const payload = (await response.json()) as EvalRunStartedResponse & {
    error?: { message?: string };
  };
  if (response.status === 409) {
    throw new Error("已有评测在运行中，请等待完成或取消后再试");
  }
  if (!response.ok) {
    throw new Error(payload.error?.message || "启动场景评测失败");
  }
  return payload;
}

export async function cancelEvalRun(runId: string): Promise<void> {
  const response = await fetch(`/api/eval/runs/${runId}/cancel`, { method: "POST" });
  if (!response.ok) {
    const payload = (await response.json()) as { error?: { message?: string } };
    throw new Error(payload.error?.message || "取消评测失败");
  }
}

export async function listEvalRuns(
  tier?: "smoke" | "judge" | "exploratory",
  signal?: AbortSignal,
): Promise<EvalRunSummary[]> {
  const params = new URLSearchParams();
  if (tier) {
    params.set("tier", tier);
  }
  const query = params.toString();
  const response = await fetch(`/api/eval/runs${query ? `?${query}` : ""}`, { signal });
  if (!response.ok) {
    throw new Error("加载运行历史失败");
  }
  return (await response.json()) as EvalRunSummary[];
}

export async function getEvalRun(runId: string): Promise<EvalRunResponse> {
  const response = await fetch(`/api/eval/runs/${runId}`);
  const payload = (await response.json()) as EvalRunResponse;
  if (!response.ok) {
    throw new Error(payload.error?.message || "加载评测详情失败");
  }
  return payload;
}
