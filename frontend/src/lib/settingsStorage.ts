import type { ChatSettings } from "@/features/chat/types";
import { getOrCreateUserId } from "./userId";

const GLOBAL_LEGACY_KEY = "gardenagent.frontend.settings.v1";

export function settingsStorageKey(userId: string): string {
  return `gardenagent.frontend.settings.v1.${userId}`;
}

export function loadSettingsForUser(userId: string): Partial<ChatSettings> {
  if (typeof window === "undefined") {
    return {};
  }
  const key = settingsStorageKey(userId);
  let raw = localStorage.getItem(key);
  if (!raw) {
    const legacy = localStorage.getItem(GLOBAL_LEGACY_KEY);
    if (legacy) {
      localStorage.setItem(key, legacy);
      localStorage.removeItem(GLOBAL_LEGACY_KEY);
      raw = legacy;
    }
  }
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw) as Partial<ChatSettings>;
  } catch {
    return {};
  }
}

export function saveSettingsForUser(userId: string, settings: ChatSettings): void {
  localStorage.setItem(settingsStorageKey(userId), JSON.stringify(settings));
}

export function removeSettingsForUser(userId: string): void {
  localStorage.removeItem(settingsStorageKey(userId));
}

export function loadSettingsForCurrentUser(): Partial<ChatSettings> {
  return loadSettingsForUser(getOrCreateUserId());
}

export function saveSettingsForCurrentUser(settings: ChatSettings): void {
  saveSettingsForUser(getOrCreateUserId(), settings);
}
