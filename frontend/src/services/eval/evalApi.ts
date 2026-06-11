import type { EmotionEvalRequest, EmotionEvalResponse } from "@/features/test/types";

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
