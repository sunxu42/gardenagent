export const USER_ID_STORAGE_KEY = "gardenagent.frontend.userId.v1";
export const LEGACY_CLIENT_STORAGE_KEY = "gardenagent.frontend.client.v1";
const USER_ID_PATTERN = /^[a-zA-Z0-9_-]{8,64}$/;

export function validateUserId(value: string): boolean {
  return USER_ID_PATTERN.test(value.trim());
}

export function generateUserId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `user_${crypto.randomUUID()}`;
  }
  const t = Date.now().toString(36);
  const r = Math.random().toString(36).slice(2, 10);
  return `user_${t}_${r}`;
}

function migrateLegacyClientId(): string | null {
  const raw = localStorage.getItem(LEGACY_CLIENT_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as { clientId?: unknown };
    if (typeof parsed.clientId === "string" && validateUserId(parsed.clientId)) {
      localStorage.setItem(USER_ID_STORAGE_KEY, parsed.clientId.trim());
      localStorage.removeItem(LEGACY_CLIENT_STORAGE_KEY);
      return parsed.clientId.trim();
    }
  } catch {
    // ignore invalid legacy cache
  }
  return null;
}

export function getOrCreateUserId(): string {
  if (typeof window === "undefined") {
    return "user_ssr_placeholder";
  }
  const existing = localStorage.getItem(USER_ID_STORAGE_KEY);
  if (existing && validateUserId(existing)) {
    return existing.trim();
  }
  const migrated = migrateLegacyClientId();
  if (migrated) {
    return migrated;
  }
  const id = generateUserId();
  localStorage.setItem(USER_ID_STORAGE_KEY, id);
  return id;
}

/** 清空成功后：写入新 id（调用方已清完服务端与旧本地数据） */
export function rotateUserId(): string {
  const id = generateUserId();
  localStorage.setItem(USER_ID_STORAGE_KEY, id);
  return id;
}
