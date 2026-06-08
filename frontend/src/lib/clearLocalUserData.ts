import { clearChatHistoryDatabase } from "@/features/chat/storage/chatHistoryDb";
import { USER_ID_STORAGE_KEY } from "./userId";
import { removeSettingsForUser } from "./settingsStorage";

const EXTRA_KEYS = ["gardenagent.config.previewRatio"] as const;

export async function clearLocalDataForUser(oldUserId: string): Promise<void> {
  removeSettingsForUser(oldUserId);
  for (const key of EXTRA_KEYS) {
    localStorage.removeItem(key);
  }
  localStorage.removeItem(USER_ID_STORAGE_KEY);
  await clearChatHistoryDatabase();
}
