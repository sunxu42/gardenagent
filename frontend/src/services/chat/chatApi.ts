import { waitForOpusModule } from "./opus/loadOpus";
import {
  buildHello,
  buildUserText,
  buildVoiceSession,
  type WsMappedEvent,
  mapEventToAction,
  mapServerMessage,
} from "./wsClient";
import type { ChatAction } from "../../features/chat/types";
import { createVoiceClient } from "./voiceClient";

export interface ChatApi {
  connect: () => void;
  disconnect: () => void;
  sendText: (text: string) => void;
  syncVoiceType: () => void;
  startVoice: () => Promise<void>;
  stopVoice: () => Promise<void>;
}

interface CreateChatApiOptions {
  url: string;
  deviceId: string;
  clientId: string;
  onAction: (action: ChatAction) => void;
  onOpen?: () => void;
  onClose?: () => void;
  getVoiceType: () => string | null;
  getAssistantMessageId: () => string | null;
  setAssistantMessageId: (id: string | null) => void;
}

export function createChatApi(options: CreateChatApiOptions): ChatApi {
  let socket: WebSocket | null = null;
  let fallbackAssistantMessageId: string | null = null;
  let voiceActive = false;
  const voiceClient = createVoiceClient();

  const ensureFallbackAssistantMessage = (): string => {
    if (!fallbackAssistantMessageId) {
      fallbackAssistantMessageId = `assistant-fallback-${Date.now()}`;
      options.onAction({
        type: "messageQueued",
        payload: {
          id: fallbackAssistantMessageId,
          role: "assistant",
          content: "",
        },
      });
    }
    return fallbackAssistantMessageId;
  };

  const applyMappedEvent = (wsEvent: WsMappedEvent) => {
    if (wsEvent.type === "HELLO") {
      options.onAction({
        type: "vadBaselineUpdated",
        payload: {
          baselineVad: wsEvent.baselineVad ?? null,
          currentVad: wsEvent.currentVad ?? null,
          relationship: wsEvent.relationship ?? null,
          emotionProfile: wsEvent.emotionProfile ?? null,
        },
      });
    }
    if (wsEvent.type === "USER_TRANSCRIPT") {
      if (!voiceActive) {
        return;
      }
      if (wsEvent.isFinal) {
        const action = mapEventToAction(wsEvent, null);
        if (action?.type === "voiceUserUtteranceFinal") {
          options.setAssistantMessageId(action.payload.assistantMessageId);
          options.onAction(action);
        }
        return;
      }
      const partialAction = mapEventToAction(wsEvent, null);
      if (partialAction) {
        options.onAction(partialAction);
      }
      return;
    }

    if ((wsEvent.type === "AUDIO_CHUNK" || wsEvent.type === "AUDIO_END") && !voiceActive) {
      return;
    }

    const primaryAssistantId = options.getAssistantMessageId();
    const needsAssistantTarget =
      wsEvent.type === "STREAM_START" || wsEvent.type === "STREAM_APPEND" || wsEvent.type === "STREAM_DONE";
    const targetAssistantId = primaryAssistantId ?? (needsAssistantTarget ? ensureFallbackAssistantMessage() : null);
    const action = mapEventToAction(wsEvent, targetAssistantId);
    if (action) {
      options.onAction(action);
    }
    if (wsEvent.type === "STREAM_DONE") {
      fallbackAssistantMessageId = null;
      options.setAssistantMessageId(null);
    }
  };

  const connect = () => {
    if (socket && socket.readyState <= WebSocket.OPEN) {
      return;
    }

    const wsUrl = new URL(options.url);
    wsUrl.searchParams.set("device-id", options.deviceId);
    wsUrl.searchParams.set("client-id", options.clientId);
    socket = new WebSocket(wsUrl.toString());
    socket.binaryType = "arraybuffer";

    socket.onopen = () => {
      options.onAction({
        type: "connectionChanged",
        payload: { status: "online" },
      });
      socket?.send(
        JSON.stringify(
          buildHello(options.deviceId, options.clientId, {
            voiceSession: false,
          }),
        ),
      );
      options.onOpen?.();
    };

    socket.onclose = () => {
      options.onAction({
        type: "connectionChanged",
        payload: { status: "offline" },
      });
      options.onClose?.();
    };

    socket.onerror = () => {
      options.onAction({
        type: "connectionChanged",
        payload: { status: "offline" },
      });
    };

    socket.onmessage = async (event) => {
      if (event.data instanceof ArrayBuffer) {
        if (voiceActive) {
          voiceClient.handleIncomingOpus(new Uint8Array(event.data));
        }
        return;
      }

      if (event.data instanceof Blob) {
        if (voiceActive) {
          const buffer = await event.data.arrayBuffer();
          voiceClient.handleIncomingOpus(new Uint8Array(buffer));
        }
        return;
      }

      let parsed: unknown;
      try {
        parsed = JSON.parse(String(event.data));
      } catch {
        return;
      }

      const raw = parsed as Record<string, unknown>;
      const wsEvent = mapServerMessage(raw);
      applyMappedEvent(wsEvent);
    };
  };

  const disconnect = () => {
    void stopVoice();
    socket?.close();
    socket = null;
  };

  const sendText = (text: string) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      options.onAction({
        type: "connectionChanged",
        payload: { status: "offline" },
      });
      return;
    }
    socket.send(JSON.stringify(buildUserText(text)));
  };

  const sendVoiceSession = (state: "start" | "stop") => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    const voiceType = state === "start" ? options.getVoiceType() ?? undefined : undefined;
    socket.send(JSON.stringify(buildVoiceSession(state, voiceType)));
  };

  const syncVoiceType = () => {
    if (!voiceActive || !socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    sendVoiceSession("start");
  };

  const startVoice = async () => {
    if (voiceActive) {
      return;
    }
    try {
      sendVoiceSession("start");
      await waitForOpusModule();
      await voiceClient.start({
        onSendOpus: (opusData) => {
          if (!socket || socket.readyState !== WebSocket.OPEN) {
            return;
          }
          socket.send(opusData);
        },
        onPlaybackStart: () => {
          options.onAction({ type: "voicePlaybackStarted" });
        },
        onPlaybackIdle: () => {
          options.onAction({ type: "voicePlaybackFinished" });
        },
      });
      voiceActive = true;
    } catch (error) {
      voiceActive = false;
      sendVoiceSession("stop");
      await voiceClient.stop().catch(() => undefined);
      options.onAction({
        type: "voiceErrorOccurred",
        payload: { message: error instanceof Error ? error.message : "语音启动失败" },
      });
    }
  };

  const stopVoice = async () => {
    if (!voiceActive) {
      return;
    }
    voiceActive = false;
    voiceClient.interruptPlayback();
    await voiceClient.stop();
    sendVoiceSession("stop");
    options.setAssistantMessageId(null);
    fallbackAssistantMessageId = null;
    options.onAction({ type: "voiceCallEnded" });
  };

  return { connect, disconnect, sendText, syncVoiceType, startVoice, stopVoice };
}
