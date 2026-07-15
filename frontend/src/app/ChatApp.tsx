import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Composer } from "../features/chat/components/Composer";
import { HeaderBar } from "../features/chat/components/HeaderBar";
import { MessageList } from "../features/chat/components/MessageList";
import { showUiActionToast } from "../features/chat/lib/uiActionToast";
import { RetryHint } from "../features/chat/components/RetryHint";
import { SettingsDrawer } from "../features/chat/components/SettingsDrawer";
import { ClearUserDataDialog } from "../features/chat/components/ClearUserDataDialog";
import { StrategyPanel } from "../features/strategy/StrategyPanel";
import { MobileStrategySheet } from "../features/strategy/MobileStrategySheet";
import { EvalRunProvider } from "../features/test/EvalRunProvider";
import { A2UIProviderShell } from "../features/chat/components/A2UIProviderShell";
import type { EvalWsEvent } from "../features/test/evalWsTypes";
import { parseStrategyPanelTab, type StrategyPanelTab } from "../features/strategy/types";
import { chatReducer, initialChatState } from "../features/chat/store/chatReducer";
import type { ChatSettings, ChatState, AppearanceMode } from "../features/chat/types";
import { useChatHistoryPersistence } from "../features/chat/hooks/useChatHistoryPersistence";
import { useChatScrollChrome } from "../features/chat/hooks/useChatScrollChrome";
import { useChatFooterInset } from "../features/chat/hooks/useChatFooterInset";
import { useStickToBottomScroll } from "../features/chat/hooks/useStickToBottomScroll";
import { DEFAULT_TTS_VOICE } from "../features/chat/ttsVoices";
import { toggleAffectLockRef } from "../features/chat/lib/emotionReference";
import { createChatApi, type ChatApi } from "../services/chat/chatApi";
import { getOrCreateUserId, rotateUserId } from "../lib/userId";
import { clearLocalDataForUser } from "../lib/clearLocalUserData";
import {
  buildUserDataClearedEntry,
  consumePendingLogAfterReload,
  stashPendingLogAfterReload,
} from "../features/logs/logUtils";
import { loadSettingsForUser, saveSettingsForUser } from "../lib/settingsStorage";
import { clearServerUserData } from "../services/userDataApi";
import { useMediaQuery } from "../lib/useMediaQuery";

const appearanceSet = new Set<AppearanceMode>(["light", "dark"]);

function isAppearanceMode(value: unknown): value is AppearanceMode {
  return typeof value === "string" && appearanceSet.has(value as AppearanceMode);
}

function mergeSettings(partial: Partial<ChatSettings>): ChatSettings {
  const voiceType = typeof partial.voiceType === "string" ? partial.voiceType.trim() : "";
  return {
    ...initialChatState.settings,
    ...partial,
    voiceType: voiceType || initialChatState.settings.voiceType || DEFAULT_TTS_VOICE,
    appearance: isAppearanceMode(partial.appearance)
      ? partial.appearance
      : initialChatState.settings.appearance,
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
  const [strategySheetOpen, setStrategySheetOpen] = useState(false);

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
  const footerRef = useRef<HTMLElement>(null);
  const { scrollRef: chatScrollRef, onScroll: onChatScroll, pinToBottom } =
    useStickToBottomScroll(state.messages);
  useChatFooterInset(footerRef, chatScrollRef);
  const { compact: chromeCompact, onScroll: onChromeScroll } = useChatScrollChrome(chatScrollRef);
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
  const evalEventDispatchRef = useRef<((event: EvalWsEvent) => void) | null>(null);
  const handleToggleAffectLock = useCallback(
    (dimension: "relationship" | "agent_vad", refId: string) => {
      const nextRef = toggleAffectLockRef(dimension, refId, state.affectLock);
      chatApiRef.current?.sendAffectLock(dimension, nextRef);
    },
    [state.affectLock],
  );
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
    const pending = consumePendingLogAfterReload();
    if (pending) {
      dispatch({ type: "logEntryReceived", payload: { entry: pending } });
    }
  }, []);

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
      onEvalEvent: (event) => {
        evalEventDispatchRef.current?.(event);
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
    const runId = `run-${turnAt}`;

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
    pinToBottom();
    chatApiRef.current?.sendText(trimmed, { messageId: assistantId, runId });
  };

  const handleClearUserData = useCallback(async () => {
    setClearBusy(true);
    setClearError(null);
    const oldUserId = userIdRef.current;
    try {
      const result = await clearServerUserData(oldUserId);
      stashPendingLogAfterReload(buildUserDataClearedEntry(oldUserId, result));
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

  const handleStrategySheetOpenChange = useCallback(
    (open: boolean) => {
      setStrategySheetOpen(open);
      if (!open && !isDesktop) {
        setSearchParams(
          (prev) => {
            const next = new URLSearchParams(prev);
            next.delete("panel");
            return next;
          },
          { replace: true },
        );
      }
    },
    [isDesktop, setSearchParams],
  );

  const strategyPanelProps = {
    activeTab: strategyTab,
    onTabChange: handleStrategyTabChange,
    history: state.affectHistory ?? [],
    currentAgentVad: state.currentAgentVad ?? null,
    baselineVad: state.baselineVad ?? null,
    emotionProfile: state.emotionProfile ?? null,
    currentRelationship: state.currentRelationship ?? null,
    affectLock: state.affectLock,
    onToggleAffectLock: handleToggleAffectLock,
    logEntries: state.logEntries,
    onClearLogs: () =>
      dispatch({
        type: "clearLogs",
        payload: { previousCount: state.logEntries.length },
      }),
  };

  return (
    <A2UIProviderShell>
    <EvalRunProvider eventDispatchRef={evalEventDispatchRef}>
    <div
      className="chat-app-shell"
      data-appearance={state.settings.appearance}
      data-font-size={state.settings.fontSize}
      data-motion={state.settings.motion}
    >
      <div className="chat-app-layout">
        <div className="chat-main-column">
        <div
          className="mobile-chat-page mobile-shell chat-ios"
          data-appearance={state.settings.appearance}
          data-scroll-compact={chromeCompact || undefined}
        >
        <header role="banner" className="chat-ios-chrome chat-ios-chrome--top">
          <HeaderBar
            agentName={agentDisplayName}
            connectionStatus={state.connectionStatus}
            onOpenSettings={() => setSettingsOpen(true)}
            onOpenStrategy={isDesktop ? undefined : () => setStrategySheetOpen(true)}
          />
        </header>
        <main
          role="main"
          className="chat-scroll-area"
          ref={chatScrollRef}
          onScroll={() => {
            onChatScroll();
            onHistoryScroll();
            onChromeScroll();
          }}
        >
          <MessageList
            messages={state.messages}
            historyLoading={historyLoading}
            hasMoreHistory={hasMoreHistory}
            connectionStatus={state.connectionStatus}
            onUiAction={(payload) => {
              if (state.connectionStatus === "offline") {
                showUiActionToast("连接已断开，请等待重连后再操作");
                return;
              }
              const target = state.messages.find((message) => message.id === payload.messageId);
              const pendingOnSurface = target?.parts.some(
                (part) =>
                  part.type === "a2ui" &&
                  part.surfaceId === payload.surfaceId &&
                  part.interaction === "pending",
              );
              if (target?.status === "done" && !pendingOnSurface) {
                showUiActionToast("会话已过期，请重新发送");
                return;
              }
              const ok = chatApiRef.current?.sendUiAction(payload);
              if (!ok) {
                showUiActionToast("会话已过期，请重新发送");
                return;
              }
              dispatch({
                type: "a2uiInteractionResolved",
                payload: {
                  messageId: payload.messageId,
                  surfaceId: payload.surfaceId,
                  action: payload.action,
                },
              });
            }}
          />
          <RetryHint visible={state.connectionStatus === "offline"} />
        </main>
        <footer
          ref={footerRef}
          role="contentinfo"
          className="chat-footer chat-ios-footer chat-ios-chrome chat-ios-chrome--bottom"
        >
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
          appearance={state.settings.appearance}
          onOpenChange={setClearDialogOpen}
          onConfirm={() => void handleClearUserData()}
        />
        </div>
        </div>
        {isDesktop ? <StrategyPanel {...strategyPanelProps} /> : null}
      </div>
      {!isDesktop ? (
        <MobileStrategySheet
          open={strategySheetOpen}
          onOpenChange={handleStrategySheetOpenChange}
          {...strategyPanelProps}
        />
      ) : null}
    </div>
    </EvalRunProvider>
    </A2UIProviderShell>
  );
}
