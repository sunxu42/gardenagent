import type {
  AffectLockSlice,
  AffectLockState,
  ChatAction,
  EmotionProfile,
  RelationshipSnapshot,
  ResponsePolicySnapshot,
  StrategyTagsSnapshot,
} from "../../features/chat/types";
import { EMPTY_AFFECT_LOCK } from "../../features/chat/types";
import type { LogEntry, LogLevel, LogModule } from "../../features/logs/logTypes";
import { LOG_LEVELS, LOG_MODULES } from "../../features/logs/logTypes";
import { parseEmotionProfile } from "../../features/chat/lib/emotionProfile";
import type { EvalWsEvent } from "../../features/test/evalWsTypes";

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
  user_affect_vad?: unknown;
  relationship?: unknown;
  agent_vad_target?: unknown;
  agent_vad_after?: unknown;
  user_weight?: unknown;
  interpersonal_cue?: unknown;
  response_policy?: unknown;
  actuation_weight?: unknown;
  synthesis_rule?: unknown;
  strategy_tags?: unknown;
  agent_emotion?: unknown;
  emotion_scale?: unknown;
  schema_version?: unknown;
  timestamp?: unknown;
  emotion?: unknown;
  ts_ms?: unknown;
  level?: unknown;
  module?: unknown;
  message?: unknown;
  extra?: unknown;
  dimension?: unknown;
  agent_vad?: unknown;
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

export function buildAffectLock(dimension: "relationship" | "agent_vad", refId: string | null) {
  return { type: "affect_lock", dimension, ref_id: refId };
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
      relationship?: RelationshipSnapshot | null;
      emotionProfile?: EmotionProfile | null;
      affectLock?: AffectLockState;
    }
  | {
      type: "AFFECT_LOCK_STATE";
      relationship: AffectLockSlice;
      agentVad: AffectLockSlice;
      relationshipSnapshot?: RelationshipSnapshot | null;
      currentVad?: { v: number; a: number; d: number } | null;
    }
  | { type: "AFFECT_LOCK_ERROR"; dimension: string; message: string }
  | {
      type: "AFFECT_TURN_APPRAISED";
      turnId: string;
      userText: string;
      timestamp: number;
      userAffectVad: { v: number; a: number; d: number };
      userWeight?: number;
      relationship?: RelationshipSnapshot;
      interpersonalCue?: string;
      responsePolicy?: ResponsePolicySnapshot;
      agentVadTarget?: { v: number; a: number; d: number } | null;
      actuationWeight?: number;
      synthesisRule?: string;
      strategyTags?: StrategyTagsSnapshot;
    }
  | {
      type: "AFFECT_TURN_SETTLED";
      turnId: string;
      timestamp: number;
      agentVadAfter: { v: number; a: number; d: number };
      agentEmotion: string;
      emotionScale: number;
    }
  | {
      type: "VAD_TURN_EVALUATED";
      turnId: string;
      userText: string;
      utteranceVad: { v: number; a: number; d: number };
      agentVadAfter: { v: number; a: number; d: number };
      timestamp: number;
    }
  | { type: "LOG_ENTRY"; entry: LogEntry }
  | { type: "EVAL_EVENT"; event: EvalWsEvent }
  | { type: "IGNORE" };

function readOptionalNumber(raw: unknown): number | undefined {
  const n = Number(raw);
  return Number.isFinite(n) ? n : undefined;
}

function readRelationship(raw: unknown): RelationshipSnapshot | undefined {
  if (!raw || typeof raw !== "object") {
    return undefined;
  }
  const rel = raw as Record<string, unknown>;
  const trust = Number(rel.trust);
  const warmth = Number(rel.warmth);
  if (!Number.isFinite(trust) || !Number.isFinite(warmth)) {
    return undefined;
  }
  return {
    trust,
    warmth,
    stage: typeof rel.stage === "string" ? rel.stage : "unknown",
    trustDelta: readOptionalNumber(rel.trust_delta),
    warmthDelta: readOptionalNumber(rel.warmth_delta),
    relWeight: readOptionalNumber(rel.rel_weight),
  };
}

function readStrategyTags(raw: unknown): StrategyTagsSnapshot | undefined {
  if (!raw || typeof raw !== "object") {
    return undefined;
  }
  const tags = raw as Record<string, unknown>;
  const mode = typeof tags.mode === "string" ? tags.mode : "";
  const voiceStyle = typeof tags.voice_style === "string" ? tags.voice_style : "";
  const length = typeof tags.length === "string" ? tags.length : "";
  const llmGuideline = typeof tags.llm_guideline === "string" ? tags.llm_guideline : "";
  const ttsProfile = typeof tags.tts_profile === "string" ? tags.tts_profile : "";
  if (!mode && !voiceStyle && !length) {
    return undefined;
  }
  return { mode, voiceStyle, length, llmGuideline, ttsProfile };
}

function readResponsePolicy(raw: unknown): ResponsePolicySnapshot | undefined {
  if (!raw || typeof raw !== "object") {
    return undefined;
  }
  const policy = raw as Record<string, unknown>;
  return {
    empathyMode: typeof policy.empathy_mode === "string" ? policy.empathy_mode : "neutral",
    stance: typeof policy.stance === "string" ? policy.stance : "balanced",
    repairAction: typeof policy.repair_action === "string" ? policy.repair_action : "none",
    directiveness: readOptionalNumber(policy.directiveness) ?? 0.5,
  };
}

function readAffectLockSlice(raw: unknown): AffectLockSlice {
  if (!raw || typeof raw !== "object") {
    return { locked: false };
  }
  const slice = raw as Record<string, unknown>;
  return {
    locked: slice.locked === true,
    refId: typeof slice.ref_id === "string" ? slice.ref_id : null,
  };
}

export function parseAffectLockState(raw: unknown): AffectLockState {
  if (!raw || typeof raw !== "object") {
    return EMPTY_AFFECT_LOCK;
  }
  const state = raw as Record<string, unknown>;
  return {
    relationship: readAffectLockSlice(state.relationship),
    agentVad: readAffectLockSlice(state.agent_vad),
  };
}

function lockSliceToRelationship(raw: unknown): RelationshipSnapshot | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }
  const slice = raw as Record<string, unknown>;
  if (slice.locked !== true) {
    return null;
  }
  const trust = Number(slice.trust);
  const warmth = Number(slice.warmth);
  if (!Number.isFinite(trust) || !Number.isFinite(warmth)) {
    return null;
  }
  return {
    trust,
    warmth,
    stage: typeof slice.stage === "string" ? slice.stage : "unknown",
  };
}

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

const LOG_LEVEL_SET = new Set<string>(LOG_LEVELS);
const LOG_MODULE_SET = new Set<string>(LOG_MODULES);

function parseLogLevel(raw: unknown): LogLevel | null {
  if (typeof raw !== "string") {
    return null;
  }
  const upper = raw.toUpperCase();
  return LOG_LEVEL_SET.has(upper) ? (upper as LogLevel) : null;
}

function parseLogModule(raw: unknown): LogModule | null {
  if (typeof raw !== "string") {
    return null;
  }
  const upper = raw.toUpperCase();
  return LOG_MODULE_SET.has(upper) ? (upper as LogModule) : null;
}

function readLogExtra(raw: unknown): Record<string, unknown> | undefined {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return undefined;
  }
  return raw as Record<string, unknown>;
}

function parseLogEntry(msg: AssistantServerMessage): LogEntry | null {
  const tsMs = Number(msg.ts_ms);
  const level = parseLogLevel(msg.level);
  const module = parseLogModule(msg.module);
  const message = typeof msg.message === "string" ? msg.message : "";
  if (!Number.isFinite(tsMs) || !level || !module || !message) {
    return null;
  }
  const turnId = typeof msg.turn_id === "string" && msg.turn_id.trim() ? msg.turn_id.trim() : undefined;
  const extra = readLogExtra(msg.extra);
  return {
    id: `log-${tsMs}-${module}-${Math.random().toString(36).slice(2, 9)}`,
    tsMs,
    level,
    module,
    message,
    turnId,
    extra,
  };
}

export function mapServerMessage(msg: AssistantServerMessage): WsMappedEvent {
  const msgType = typeof msg?.type === "string" ? msg.type : "";
  if (msgType.startsWith("eval_")) {
    return { type: "EVAL_EVENT", event: msg as EvalWsEvent };
  }

  if (msg?.type === "log_entry") {
    const entry = parseLogEntry(msg);
    if (!entry) {
      return { type: "IGNORE" };
    }
    return { type: "LOG_ENTRY", entry };
  }

  if (msg?.type === "affect_turn_appraised") {
    const turnId = typeof msg.turn_id === "string" ? msg.turn_id.trim() : "";
    const userText = typeof msg.user_text === "string" ? msg.user_text : "";
    const userAffectVad = readVadPoint(msg.user_affect_vad);
    const timestampRaw = Number(msg.timestamp);
    const timestamp = Number.isFinite(timestampRaw) ? timestampRaw : Date.now();
    const relationship = readRelationship(msg.relationship);
    if (!turnId || !userAffectVad || !relationship) {
      return { type: "IGNORE" };
    }
    return {
      type: "AFFECT_TURN_APPRAISED",
      turnId,
      userText,
      timestamp,
      userAffectVad,
      userWeight: readOptionalNumber(msg.user_weight),
      relationship,
      interpersonalCue: typeof msg.interpersonal_cue === "string" ? msg.interpersonal_cue : undefined,
      responsePolicy: readResponsePolicy(msg.response_policy),
      agentVadTarget: readVadPoint(msg.agent_vad_target),
      actuationWeight: readOptionalNumber(msg.actuation_weight),
      synthesisRule: typeof msg.synthesis_rule === "string" ? msg.synthesis_rule : undefined,
      strategyTags: readStrategyTags(msg.strategy_tags),
    };
  }

  if (msg?.type === "affect_turn_settled") {
    const turnId = typeof msg.turn_id === "string" ? msg.turn_id.trim() : "";
    const agentVadAfter = readVadPoint(msg.agent_vad_after);
    const timestampRaw = Number(msg.timestamp);
    const timestamp = Number.isFinite(timestampRaw) ? timestampRaw : Date.now();
    if (!turnId || !agentVadAfter) {
      return { type: "IGNORE" };
    }
    return {
      type: "AFFECT_TURN_SETTLED",
      turnId,
      timestamp,
      agentVadAfter,
      agentEmotion: typeof msg.agent_emotion === "string" ? msg.agent_emotion : "neutral",
      emotionScale: readOptionalNumber(msg.emotion_scale) ?? 4,
    };
  }

  if (msg?.type === "affect_lock_state") {
    const lockState = parseAffectLockState(msg);
    const agentVadRaw = msg.agent_vad;
    const currentVad =
      agentVadRaw && typeof agentVadRaw === "object" && (agentVadRaw as Record<string, unknown>).locked === true
        ? readVadPoint((agentVadRaw as Record<string, unknown>).vad)
        : null;
    return {
      type: "AFFECT_LOCK_STATE",
      relationship: lockState.relationship,
      agentVad: lockState.agentVad,
      relationshipSnapshot: lockSliceToRelationship(msg.relationship),
      currentVad,
    };
  }

  if (msg?.type === "affect_lock_error") {
    return {
      type: "AFFECT_LOCK_ERROR",
      dimension: typeof msg.dimension === "string" ? msg.dimension : "",
      message: typeof msg.message === "string" ? msg.message : "锁定失败",
    };
  }

  if (msg?.type === "vad_turn_evaluated") {
    const turnId = typeof msg.turn_id === "string" ? msg.turn_id.trim() : "";
    const userText = typeof msg.user_text === "string" ? msg.user_text : "";
    const utteranceVad = readVadPoint(msg.user_affect_vad ?? msg.utterance_vad);
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
    const relationship = readRelationship(emotion?.relationship) ?? null;
    const emotionProfile = parseEmotionProfile(emotion?.profile) ?? null;
    const affectLock = parseAffectLockState(emotion?.affect_lock);
    return {
      type: "HELLO",
      sessionId: msg.session_id,
      paramVersion: msg.param_version,
      supportedVoices,
      currentVoice,
      baselineVad,
      currentVad,
      relationship,
      emotionProfile,
      affectLock,
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

  if (event.type === "AFFECT_TURN_APPRAISED") {
    return {
      type: "affectTurnAppraised",
      payload: {
        turnId: event.turnId,
        userText: event.userText,
        timestamp: event.timestamp,
        userAffectVad: event.userAffectVad,
        userWeight: event.userWeight,
        relationship: event.relationship,
        interpersonalCue: event.interpersonalCue,
        responsePolicy: event.responsePolicy,
        agentVadTarget: event.agentVadTarget,
        actuationWeight: event.actuationWeight,
        synthesisRule: event.synthesisRule,
        strategyTags: event.strategyTags,
      },
    };
  }

  if (event.type === "AFFECT_TURN_SETTLED") {
    return {
      type: "affectTurnSettled",
      payload: {
        turnId: event.turnId,
        timestamp: event.timestamp,
        agentVadAfter: event.agentVadAfter,
        agentEmotion: event.agentEmotion,
        emotionScale: event.emotionScale,
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

  if (event.type === "LOG_ENTRY") {
    return {
      type: "logEntryReceived",
      payload: { entry: event.entry },
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
