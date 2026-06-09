import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Composer } from "../features/chat/components/Composer";
import { HeaderBar } from "../features/chat/components/HeaderBar";
import { MessageList } from "../features/chat/components/MessageList";
import { RetryHint } from "../features/chat/components/RetryHint";
import { SettingsDrawer } from "../features/chat/components/SettingsDrawer";
import { ClearUserDataDialog } from "../features/chat/components/ClearUserDataDialog";
import { StrategyPanel } from "../features/strategy/StrategyPanel";
import { parseStrategyPanelTab, type StrategyPanelTab } from "../features/strategy/types";
import { chatReducer, initialChatState } from "../features/chat/store/chatReducer";
import type { ChatSettings, ChatState, ThemeName } from "../features/chat/types";
import { useChatHistoryPersistence } from "../features/chat/hooks/useChatHistoryPersistence";
import { useStickToBottomScroll } from "../features/chat/hooks/useStickToBottomScroll";
import { DEFAULT_TTS_VOICE } from "../features/chat/ttsVoices";
import { createChatApi, type ChatApi } from "../services/chat/chatApi";
import { getOrCreateUserId, rotateUserId } from "../lib/userId";
import { clearLocalDataForUser } from "../lib/clearLocalUserData";
import { loadSettingsForUser, saveSettingsForUser } from "../lib/settingsStorage";
import { clearServerUserData } from "../services/userDataApi";
import { useMediaQuery } from "../lib/useMediaQuery";

const themeSet = new Set<ThemeName>(["mint-cute", "pink-blossom", "gray-mist", "orange-sunrise"]);

function isThemeName(value: unknown): value is ThemeName {
  return typeof value === "string" && themeSet.has(value as ThemeName);
}

function mergeSettings(partial: Partial<ChatSettings>): ChatSettings {
  const voiceType = typeof partial.voiceType === "string" ? partial.voiceType.trim() : "";
  return {
    ...initialChatState.settings,
    ...partial,
    voiceType: voiceType || initialChatState.settings.voiceType || DEFAULT_TTS_VOICE,
    theme: isThemeName(partial.theme) ? partial.theme : initialChatState.settings.theme,
  };
}

function initChatState(): ChatState {
  if (typeof window === "undefined") {
    return initialChatState;
  }
  const userId = getOrCreateUserId();
  return {
    ...initialChatState,
    settings: mergeSettings(loadSettingsForUser(userId)),
  };
}

export function ChatApp() {
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const [searchParams, setSearchParams] = useSearchParams();
  const strategyTab = parseStrategyPanelTab(searchParams.get("panel")) ?? "emotion";

  const panelParam = searchParams.get("panel");

  useEffect(() => {
    if (isDesktop || !panelParam) {
      return;
    }
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete("panel");
        return next;
      },
      { replace: true },
    );
  }, [isDesktop, panelParam, setSearchParams]);

  const handleStrategyTabChange = useCallback(
    (tab: StrategyPanelTab) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (tab === "emotion") {
            next.delete("panel");
          } else {
            next.set("panel", tab);
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const [state, dispatch] = useReducer(chatReducer, undefined, initChatState);
  const userIdRef = useRef(
    typeof window !== "undefined" ? getOrCreateUserId() : "user_ssr_placeholder",
  );
  const voiceTypeRef = useRef("");
  const { scrollRef: chatScrollRef, onScroll: onChatScroll } = useStickToBottomScroll(state.messages);
  const { historyLoading, hasMoreHistory, onHistoryScroll } = useChatHistoryPersistence({
    userId: userIdRef.current,
    messages: state.messages,
    dispatch,
    scrollRef: chatScrollRef,
  });
  const agentDisplayName = useMemo(() => {
    for (let i = state.messages.length - 1; i >= 0; i -= 1) {
      const message = state.messages[i];
      if (message.role === "assistant" && message.authorLabel) {
        return message.authorLabel;
      }
    }
    return "助手";
  }, [state.messages]);
  const chatApiRef = useRef<ChatApi | null>(null);
  const assistantMessageIdRef = useRef<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearBusy, setClearBusy] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);
  const wsUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return "ws://localhost/ws";
    }
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}/ws`;
  }, []);

  useEffect(() => {
    voiceTypeRef.current = state.settings.voiceType;
  }, [state.settings.voiceType]);

  useEffect(() => {
    saveSettingsForUser(userIdRef.current, state.settings);
  }, [state.settings]);

  useEffect(() => {
    const chatApi = createChatApi({
      url: wsUrl,
      deviceId: userIdRef.current,
      clientId: userIdRef.current,
      onAction: dispatch,
      getVoiceType: () => voiceTypeRef.current || null,
      getAssistantMessageId: () => assistantMessageIdRef.current,
      setAssistantMessageId: (id) => {
        assistantMessageIdRef.current = id;
      },
    });
    chatApiRef.current = chatApi;
    chatApi.connect();
    return () => {
      chatApi.disconnect();
      chatApiRef.current = null;
    };
  }, [wsUrl]);

  useEffect(() => {
    if (!chatApiRef.current || !state.voiceCallActive) {
      return;
    }
    chatApiRef.current.syncVoiceType();
  }, [state.settings.voiceType, state.voiceCallActive]);

  const handleSend = () => {
    const trimmed = state.inputValue.trim();
    if (!trimmed) {
      return;
    }

    const turnAt = Date.now();
    const userMessageId = `user-${turnAt}`;
    const assistantId = `assistant-${turnAt}`;

    dispatch({
      type: "messageQueued",
      payload: {
        id: userMessageId,
        role: "user",
        content: trimmed,
      },
    });

    dispatch({
      type: "messageQueued",
      payload: {
        id: assistantId,
        role: "assistant",
        content: "",
      },
    });
    assistantMessageIdRef.current = assistantId;

    dispatch({
      type: "inputChanged",
      payload: {
        value: "",
      },
    });
    chatApiRef.current?.sendText(trimmed);
  };

  const handleClearUserData = useCallback(async () => {
    setClearBusy(true);
    setClearError(null);
    const oldUserId = userIdRef.current;
    try {
      await clearServerUserData(oldUserId);
      await clearLocalDataForUser(oldUserId);
      rotateUserId();
      window.location.reload();
    } catch (error) {
      setClearError(error instanceof Error ? error.message : "清空失败");
      setClearBusy(false);
    }
  }, []);

  const startVoiceCall = () => {
    if (state.voiceCallActive) {
      return;
    }
    dispatch({ type: "voiceListeningStarted" });
    void chatApiRef.current?.startVoice();
  };

  const endVoiceCall = () => {
    void chatApiRef.current?.stopVoice();
  };

  return (
    <div
      className="chat-app-shell"
      data-theme={state.settings.theme}
      data-font-size={state.settings.fontSize}
      data-motion={state.settings.motion}
    >
      <div className="chat-app-layout">
        <div className="chat-main-column">
        <div className="mobile-chat-page mobile-shell" data-theme={state.settings.theme}>
        <header role="banner">
          <HeaderBar
            agentName={agentDisplayName}
            connectionStatus={state.connectionStatus}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        </header>
        <main
          role="main"
          className="chat-scroll-area"
          ref={chatScrollRef}
          onScroll={() => {
            onChatScroll();
            onHistoryScroll();
          }}
        >
          <MessageList
            messages={state.messages}
            historyLoading={historyLoading}
            hasMoreHistory={hasMoreHistory}
          />
          <RetryHint visible={state.connectionStatus === "offline"} />
        </main>
        <footer role="contentinfo" className="chat-footer">
          <Composer
            value={state.inputValue}
            voiceError={state.voiceError}
            onChange={(value) =>
              dispatch({
                type: "inputChanged",
                payload: { value },
              })
            }
            onSend={handleSend}
            voiceCallActive={state.voiceCallActive}
            voiceState={state.voiceState}
            onStartVoiceCall={startVoiceCall}
            onEndVoiceCall={endVoiceCall}
          />
        </footer>
        <SettingsDrawer
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          settings={state.settings}
          onSettingsChange={(settings) => dispatch({ type: "settingsChanged", payload: { settings } })}
          onRequestClearUserData={() => {
            setClearError(null);
            setClearDialogOpen(true);
          }}
        />
        <ClearUserDataDialog
          open={clearDialogOpen}
          busy={clearBusy}
          error={clearError}
          onOpenChange={setClearDialogOpen}
          onConfirm={() => void handleClearUserData()}
        />
        </div>
        </div>
        {isDesktop ? (
          <StrategyPanel
            activeTab={strategyTab}
            onTabChange={handleStrategyTabChange}
            history={state.affectHistory ?? []}
            currentAgentVad={state.currentAgentVad ?? null}
            baselineVad={state.baselineVad ?? null}
            emotionProfile={state.emotionProfile ?? null}
            currentRelationship={state.currentRelationship ?? null}
          />
        ) : null}
      </div>
    </div>
  );
}
