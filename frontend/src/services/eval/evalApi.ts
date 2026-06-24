import type { EmotionEvalRequest, EmotionEvalResponse } from "@/features/test/types";
import type { EvalRunStartedResponse } from "@/features/test/types";

export async function startExploratoryEvalAsync(
  request: EmotionEvalRequest,
  clientId: string,
): Promise<EvalRunStartedResponse> {
  const response = await fetch("/api/eval/emotion-support/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...request,
      client_id: clientId,
      async: true,
    }),
  });
  const payload = (await response.json()) as EvalRunStartedResponse & {
    error?: { message?: string };
  };
  if (response.status === 409) {
    throw new Error("已有评测在运行中，请等待完成或取消后再试");
  }
  if (!response.ok) {
    throw new Error(payload.error?.message || "启动情绪探索评测失败");
  }
  return payload;
}

/** @deprecated Use startExploratoryEvalAsync for live progress */
export async function runEmotionEval(request: EmotionEvalRequest): Promise<EmotionEvalResponse> {
  const response = await fetch("/api/eval/emotion-support/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  let payload: EmotionEvalResponse;
  try {
    payload = (await response.json()) as EmotionEvalResponse;
  } catch {
    throw new Error("评测运行失败");
  }

  if (!response.ok || payload.status === "failed") {
    throw new Error(payload.error?.message || "评测运行失败");
  }

  return payload;
}
