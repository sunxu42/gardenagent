import { normalizeLegacyCreatedAt } from "./chatMessageOrder";
import type { StoredChatMessage } from "./chatHistoryTypes";
import {
  CHAT_HISTORY_DB_NAME,
  CHAT_HISTORY_FETCH_BATCH,
  CHAT_HISTORY_INDEX_USER_TIME,
  CHAT_HISTORY_STORE,
} from "./chatHistoryTypes";

let dbPromise: Promise<IDBDatabase> | null = null;

function openDatabase(): Promise<IDBDatabase> {
  if (typeof indexedDB === "undefined") {
    return Promise.reject(new Error("indexedDB is not available"));
  }
  if (dbPromise) {
    return dbPromise;
  }

  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(CHAT_HISTORY_DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(CHAT_HISTORY_STORE)) {
        const store = db.createObjectStore(CHAT_HISTORY_STORE, { keyPath: "id" });
        store.createIndex(CHAT_HISTORY_INDEX_USER_TIME, ["userId", "createdAt"]);
      }
    };
    request.onblocked = () => undefined;
    request.onsuccess = () => {
      resolve(request.result);
    };
    request.onerror = () => {
      reject(request.error ?? new Error("indexedDB open failed"));
    };
  });

  return dbPromise;
}

function runTransaction<T>(
  mode: IDBTransactionMode,
  run: (store: IDBObjectStore) => IDBRequest<T> | void,
): Promise<T | void> {
  return openDatabase().then(
    (db) =>
      new Promise<T | void>((resolve, reject) => {
        const tx = db.transaction(CHAT_HISTORY_STORE, mode);
        const store = tx.objectStore(CHAT_HISTORY_STORE);
        const request = run(store);
        tx.oncomplete = () => {
          if (request && "result" in request) {
            resolve((request as IDBRequest<T>).result);
          } else {
            resolve(undefined);
          }
        };
        tx.onerror = () => reject(tx.error ?? new Error("indexedDB transaction failed"));
      }),
  );
}

export async function upsertChatMessages(messages: StoredChatMessage[]): Promise<void> {
  if (messages.length === 0) {
    return;
  }
  await runTransaction("readwrite", (store) => {
    for (const message of messages) {
      store.put(message);
    }
  });
}

/** 按时间升序返回：若 beforeCreatedAt 有值则仅返回更早的消息（取紧邻其前的最多 limit 条）。 */
export async function fetchMessagesForUser(
  userId: string,
  options: { beforeCreatedAt?: number; limit?: number } = {},
): Promise<StoredChatMessage[]> {
  const limit = options.limit ?? CHAT_HISTORY_FETCH_BATCH;
  const before = options.beforeCreatedAt;

  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(CHAT_HISTORY_STORE, "readonly");
    const index = tx.objectStore(CHAT_HISTORY_STORE).index(CHAT_HISTORY_INDEX_USER_TIME);
    const range = IDBKeyRange.bound([userId, 0], [userId, Number.MAX_SAFE_INTEGER]);
    const request = index.getAll(range);

    request.onsuccess = () => {
      let list = (request.result as StoredChatMessage[]).slice();
      list = list.map((message) => {
        const createdAt = normalizeLegacyCreatedAt(message.createdAt, message.id);
        return createdAt === message.createdAt ? message : { ...message, createdAt };
      });
      list.sort((a, b) => a.createdAt - b.createdAt);
      if (before !== undefined) {
        list = list.filter((message) => message.createdAt < before);
      }
      resolve(list.slice(Math.max(0, list.length - limit)));
    };
    request.onerror = () => reject(request.error ?? new Error("indexedDB getAll failed"));
  });
}

/** 测试用：清空库 */
export async function clearChatHistoryDatabase(): Promise<void> {
  if (dbPromise) {
    try {
      const db = await dbPromise;
      db.close();
    } catch {
      // ignore
    }
  }
  dbPromise = null;
  if (typeof indexedDB === "undefined") {
    return;
  }
  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.deleteDatabase(CHAT_HISTORY_DB_NAME);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error ?? new Error("deleteDatabase failed"));
  });
}
