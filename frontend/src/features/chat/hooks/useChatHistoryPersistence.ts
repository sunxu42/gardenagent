import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import type { ChatAction, ChatMessage } from "../types";
import {
  loadOlderChatHistory,
  loadRecentChatHistory,
  persistChatMessages,
} from "../storage/chatHistoryService";

const PERSIST_DEBOUNCE_MS = 400;
const SCROLL_LOAD_THRESHOLD_PX = 72;

interface UseChatHistoryPersistenceOptions {
  userId: string;
  messages: ChatMessage[];
  dispatch: React.Dispatch<ChatAction>;
  scrollRef: RefObject<HTMLElement>;
}

export function useChatHistoryPersistence({
  userId,
  messages,
  dispatch,
  scrollRef,
}: UseChatHistoryPersistenceOptions) {
  const [historyLoading, setHistoryLoading] = useState(false);
  const [hasMoreHistory, setHasMoreHistory] = useState(false);
  const hydratedRef = useRef(false);
  const loadingOlderRef = useRef(false);
  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestMessagesRef = useRef<ChatMessage[]>(messages);
  const lastPersistedSnapshotRef = useRef("");

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const { messages: recent, hasMore } = await loadRecentChatHistory(userId);
        if (cancelled) {
          return;
        }
        if (recent.length > 0) {
          dispatch({ type: "historyHydrated", payload: { messages: recent } });
        }
        setHasMoreHistory(hasMore);
        hydratedRef.current = true;
      } catch {
        hydratedRef.current = true;
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [userId, dispatch]);

  useEffect(() => {
    latestMessagesRef.current = messages;

    if (!hydratedRef.current) {
      return;
    }

    const snapshot = messages
      .filter((m) => m.content.trim())
      .map((m) => `${m.id}:${m.status}:${m.content.length}`)
      .join("|");
    if (snapshot === lastPersistedSnapshotRef.current) {
      return;
    }

    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current);
    }

    persistTimerRef.current = setTimeout(() => {
      persistTimerRef.current = null;
      lastPersistedSnapshotRef.current = snapshot;
      void persistChatMessages(messages, userId).catch(() => {
        lastPersistedSnapshotRef.current = "";
      });
    }, PERSIST_DEBOUNCE_MS);

    return () => {
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
        persistTimerRef.current = null;
        // 在依赖变化清理阶段立即冲刷一次，避免因路由跳转丢失最近一次修改。
        lastPersistedSnapshotRef.current = snapshot;
        void persistChatMessages(latestMessagesRef.current, userId).catch(() => {
          lastPersistedSnapshotRef.current = "";
        });
      }
    };
  }, [messages, userId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const flushNow = () => {
      if (!hydratedRef.current) {
        return;
      }
      const messagesToPersist = latestMessagesRef.current;
      const snapshot = messagesToPersist
        .filter((m) => m.content.trim())
        .map((m) => `${m.id}:${m.status}:${m.content.length}`)
        .join("|");
      if (!snapshot || snapshot === lastPersistedSnapshotRef.current) {
        return;
      }
      lastPersistedSnapshotRef.current = snapshot;
      void persistChatMessages(messagesToPersist, userId).catch(() => {
        lastPersistedSnapshotRef.current = "";
      });
    };

    const handleBeforeUnload = () => {
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
        persistTimerRef.current = null;
      }
      flushNow();
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        if (persistTimerRef.current) {
          clearTimeout(persistTimerRef.current);
          persistTimerRef.current = null;
        }
        flushNow();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [userId]);

  const loadOlder = useCallback(async () => {
    if (!hasMoreHistory || loadingOlderRef.current || messages.length === 0) {
      return;
    }

    const scrollEl = scrollRef.current;
    const prevScrollHeight = scrollEl?.scrollHeight ?? 0;

    loadingOlderRef.current = true;
    setHistoryLoading(true);
    try {
      const { messages: older, hasMore } = await loadOlderChatHistory(userId, messages);
      if (older.length > 0) {
        dispatch({ type: "historyPrepended", payload: { messages: older } });
        requestAnimationFrame(() => {
          const el = scrollRef.current;
          if (el && prevScrollHeight > 0) {
            el.scrollTop += el.scrollHeight - prevScrollHeight;
          }
        });
        setHasMoreHistory(hasMore);
      } else {
        setHasMoreHistory(false);
      }
    } catch {
      // 保持当前 hasMore，允许用户再次上滑重试
    } finally {
      loadingOlderRef.current = false;
      setHistoryLoading(false);
    }
  }, [dispatch, hasMoreHistory, messages, scrollRef, userId]);

  const onHistoryScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el || !hasMoreHistory || historyLoading) {
      return;
    }
    if (el.scrollTop <= SCROLL_LOAD_THRESHOLD_PX) {
      void loadOlder();
    }
  }, [hasMoreHistory, historyLoading, loadOlder, scrollRef]);

  return {
    historyLoading,
    hasMoreHistory,
    onHistoryScroll,
  };
}
