import type { ChatAction } from "../../features/chat/types";

export interface AssistantServerMessage {
  role?: string;
  content?: unknown;
  agent_name?: string;
  type?: string;
  msg_type?: string;
  response?: unknown;
  session_id?: string;
  param_version?: string | number;
  tts?: unknown;
  is_final?: boolean;
  source?: string;
  turn_id?: string;
  user_text?: string;
  utterance_vad?: unknown;
  agent_vad_after?: unknown;
  timestamp?: unknown;
  emotion?: unknown;
}

export interface HelloOptions {
  voiceType?: string;
  voiceSession?: boolean;
}

export function buildHello(deviceId: string, clientId: string, options: HelloOptions = {}) {
  const payload: Record<string, unknown> = {
    role: "hello",
    device_id: deviceId,
    client_id: clientId,
    device_name: "frontend-chat",
    features: { mcp: true },
    voice_session: options.voiceSession === true,
  };
  if (options.voiceSession && options.voiceType?.trim()) {
    payload.voice_type = options.voiceType.trim();
  }
  return payload;
}

export function buildUserText(text: string) {
  return {
    role: "user",
    content: [{ type: "text", text }],
  };
}

export function buildVoiceSession(state: "start" | "stop", voiceType?: string) {
  const payload: Record<string, unknown> = {
    type: "voice_session",
    state,
  };
  if (state === "start" && voiceType?.trim()) {
    payload.voice_type = voiceType.trim();
  }
  return payload;
}

export type WsMappedEvent =
  | { type: "STREAM_START"; agentName?: string }
  | { type: "STREAM_APPEND"; chunk: string; agentName?: string }
  | { type: "STREAM_DONE"; agentName?: string }
  | { type: "USER_TRANSCRIPT"; text: string; isFinal: boolean }
  | { type: "AUDIO_CHUNK" }
  | { type: "AUDIO_END" }
  | {
      type: "HELLO";
      sessionId?: string;
      paramVersion?: string | number;
      supportedVoices?: string[];
      currentVoice?: string;
      baselineVad?: { v: number; a: number; d: number } | null;
      currentVad?: { v: number; a: number; d: number } | null;
    }
  | {
      type: "VAD_TURN_EVALUATED";
      turnId: string;
      userText: string;
      utteranceVad: { v: number; a: number; d: number };
      agentVadAfter: { v: number; a: number; d: number };
      timestamp: number;
    }
  | { type: "IGNORE" };

function readVadPoint(raw: unknown): { v: number; a: number; d: number } | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }
  const point = raw as Record<string, unknown>;
  const v = Number(point.v);
  const a = Number(point.a);
  const d = Number(point.d);
  if (!Number.isFinite(v) || !Number.isFinite(a) || !Number.isFinite(d)) {
    return null;
  }
  return { v, a, d };
}

function extractTextContent(content: unknown): string {
  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {
    const textParts = content
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (
          item &&
          typeof item === "object" &&
          "type" in item &&
          "text" in item &&
          (item as { type?: unknown }).type === "text"
        ) {
          return String((item as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .filter(Boolean);
    return textParts.join("");
  }

  return "";
}

function readAgentName(...sources: unknown[]): string | undefined {
  for (const source of sources) {
    if (!source || typeof source !== "object") {
      continue;
    }
    const name = (source as { agent_name?: unknown }).agent_name;
    if (typeof name === "string" && name.trim()) {
      return name.trim();
    }
  }
  return undefined;
}

export function mapServerMessage(msg: AssistantServerMessage): WsMappedEvent {
  if (msg?.type === "vad_turn_evaluated") {
    const turnId = typeof msg.turn_id === "string" ? msg.turn_id.trim() : "";
    const userText = typeof msg.user_text === "string" ? msg.user_text : "";
    const utteranceVad = readVadPoint(msg.utterance_vad);
    const agentVadAfter = readVadPoint(msg.agent_vad_after);
    const timestampRaw = Number(msg.timestamp);
    const timestamp = Number.isFinite(timestampRaw) ? timestampRaw : Date.now();
    if (!turnId || !utteranceVad || !agentVadAfter) {
      return { type: "IGNORE" };
    }
    return { type: "VAD_TURN_EVALUATED", turnId, userText, utteranceVad, agentVadAfter, timestamp };
  }
  if (msg?.role === "user" && msg.source === "asr") {
    const text = extractTextContent(msg.content);
    if (!text) {
      return { type: "IGNORE" };
    }
    return { type: "USER_TRANSCRIPT", text, isFinal: Boolean(msg.is_final) };
  }

  if (msg?.msg_type === "response" && msg.response && typeof msg.response === "object") {
    const wrapped = msg.response as { role?: unknown; content?: unknown; agent_name?: unknown };
    const agentName = readAgentName(msg, wrapped);
    if (wrapped.role === "assistant") {
      const text = extractTextContent(wrapped.content);
      if (text === "SENTENCE_START") {
        return { type: "STREAM_START", agentName };
      }
      if (text === "SENTENCE_END") {
        return { type: "STREAM_DONE", agentName };
      }
      if (text) {
        return { type: "STREAM_APPEND", chunk: text, agentName };
      }
    }
    return { type: "IGNORE" };
  }

  if (msg?.msg_type === "SENTENCE_START") {
    return { type: "STREAM_START", agentName: readAgentName(msg) };
  }

  if (msg?.msg_type === "SENTENCE_END") {
    return { type: "STREAM_DONE", agentName: readAgentName(msg) };
  }

  if (msg?.type === "hello") {
    const tts = msg.tts && typeof msg.tts === "object" ? (msg.tts as Record<string, unknown>) : null;
    const supportedVoicesRaw = tts?.supported_voices;
    const supportedVoices = Array.isArray(supportedVoicesRaw)
      ? supportedVoicesRaw
          .map((value) => (typeof value === "string" ? value.trim() : ""))
          .filter((value): value is string => Boolean(value))
      : undefined;
    const currentVoiceRaw = tts?.current_voice;
    const currentVoice =
      typeof currentVoiceRaw === "string" && currentVoiceRaw.trim() ? currentVoiceRaw.trim() : undefined;
    const emotion = msg.emotion && typeof msg.emotion === "object" ? (msg.emotion as Record<string, unknown>) : null;
    const baselineVad = readVadPoint(emotion?.baseline_vad ?? null);
    const currentVad = readVadPoint(emotion?.current_vad ?? null);
    return {
      type: "HELLO",
      sessionId: msg.session_id,
      paramVersion: msg.param_version,
      supportedVoices,
      currentVoice,
      baselineVad,
      currentVad,
    };
  }

  if (msg?.role !== "assistant") {
    if (msg?.type === "audio_chunk") {
      return { type: "AUDIO_CHUNK" };
    }
    if (msg?.type === "audio_end") {
      return { type: "AUDIO_END" };
    }
    return { type: "IGNORE" };
  }

  const agentName = readAgentName(msg);
  const text = extractTextContent(msg.content);
  if (text === "SENTENCE_START") {
    return { type: "STREAM_START", agentName };
  }
  if (text === "SENTENCE_END") {
    return { type: "STREAM_DONE", agentName };
  }
  if (text) {
    return { type: "STREAM_APPEND", chunk: text, agentName };
  }
  return { type: "IGNORE" };
}

export function mapEventToAction(
  event: WsMappedEvent,
  assistantMessageId: string | null
): ChatAction | null {
  if (event.type === "USER_TRANSCRIPT") {
    if (event.isFinal) {
      const stamp = Date.now();
      return {
        type: "voiceUserUtteranceFinal",
        payload: {
          text: event.text,
          userMessageId: `user-voice-${stamp}`,
          assistantMessageId: `assistant-voice-${stamp}`,
        },
      };
    }
    return {
      type: "voiceTranscriptUpdated",
      payload: { text: event.text },
    };
  }

  if (event.type === "HELLO") {
    // 同一个 hello 事件拆分成两条 action，调用方会按顺序 dispatch
    return {
      type: "voiceCatalogUpdated",
      payload: {
        voices: event.supportedVoices ?? [],
        currentVoice: event.currentVoice,
      },
    };
  }

  if (event.type === "VAD_TURN_EVALUATED") {
    return {
      type: "vadTurnEvaluated",
      payload: {
        turnId: event.turnId,
        userText: event.userText,
        utteranceVad: event.utteranceVad,
        agentVadAfter: event.agentVadAfter,
        timestamp: event.timestamp,
      },
    };
  }

  if (!assistantMessageId) {
    return null;
  }

  if (event.type === "STREAM_START") {
    return {
      type: "messageStreamStart",
      payload: { id: assistantMessageId, agentName: event.agentName },
    };
  }

  if (event.type === "STREAM_APPEND") {
    return {
      type: "messageStreaming",
      payload: {
        id: assistantMessageId,
        content: event.chunk,
        agentName: event.agentName,
      },
    };
  }

  if (event.type === "STREAM_DONE") {
    return {
      type: "messageDone",
      payload: { id: assistantMessageId },
    };
  }

  if (event.type === "AUDIO_CHUNK") {
    return { type: "voicePlaybackStarted" };
  }

  if (event.type === "AUDIO_END") {
    return { type: "voicePlaybackFinished" };
  }

  return null;
}
