const CLEAR_URL = "/api/prompt-editor/user-data/clear";

export async function clearServerUserData(userId: string): Promise<Record<string, unknown>> {
  const response = await fetch(CLEAR_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  const body = (await response.json().catch(() => ({}))) as {
    ok?: boolean;
    error?: string;
    result?: Record<string, unknown>;
  };
  if (!response.ok) {
    throw new Error(body.error || `清空服务端数据失败 (${response.status})`);
  }
  return body.result ?? body;
}
