import type { AffectTurnRecord, ChatAction, ChatMessage, ChatState } from "../types";
import { baseAgentVadForDelta, computeVadDelta, upsertAffectRecord } from "../lib/affectMerge";
import { DEFAULT_TTS_VOICE } from "../ttsVoices";

export const initialChatState: ChatState = {
  messages: [],
  inputValue: "",
  connectionStatus: "online",
  availableVoices: [],
  voiceCallActive: false,
  voiceState: "idle",
  voiceTranscript: "",
  voiceError: null,
  affectHistory: [],
  currentAgentVad: null,
  baselineVad: null,
  emotionProfile: null,
  currentRelationship: null,
  settings: {
    voiceEnabled: true,
    autoPlayVoice: true,
    voiceType: DEFAULT_TTS_VOICE,
    fontSize: "normal",
    motion: "normal",
    theme: "mint-cute",
  },
};

function updateMessage(
  messages: ChatMessage[],
  id: string,
  updater: (message: ChatMessage) => ChatMessage
): ChatMessage[] {
  return messages.map((message) => (message.id === id ? updater(message) : message));
}

function mergeHistoryMessages(
  current: ChatMessage[],
  incoming: ChatMessage[],
): ChatMessage[] {
  if (incoming.length === 0) {
    return current;
  }
  const existingIds = new Set(current.map((message) => message.id));
  const older = incoming.filter((message) => !existingIds.has(message.id));
  if (older.length === 0) {
    return current;
  }
  return [...older, ...current];
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "inputChanged":
      return {
        ...state,
        inputValue: action.payload.value,
      };
    case "messageQueued":
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            id: action.payload.id,
            role: action.payload.role,
            content: action.payload.content,
            status: "sending",
          },
        ],
      };
    case "messageStreamStart": {
      const target = state.messages.find((message) => message.id === action.payload.id);
      if (target?.status === "done") {
        return state;
      }
      return {
        ...state,
        messages: updateMessage(state.messages, action.payload.id, (message) => ({
          ...message,
          status: "streaming",
          content: "",
          ...(action.payload.agentName
            ? { authorLabel: action.payload.agentName }
            : {}),
        })),
      };
    }
    case "messageStreaming":
      return {
        ...state,
        messages: updateMessage(state.messages, action.payload.id, (message) => ({
          ...message,
          status: "streaming",
          content: message.content + action.payload.content,
          ...(action.payload.agentName ? { authorLabel: action.payload.agentName } : {}),
        })),
      };
    case "messageDone":
      return {
        ...state,
        messages: updateMessage(state.messages, action.payload.id, (message) => ({
          ...message,
          status: "done",
        })),
      };
    case "connectionChanged":
      return {
        ...state,
        connectionStatus: action.payload.status,
      };
    case "voiceListeningStarted":
      return {
        ...state,
        voiceCallActive: true,
        voiceState: "listening",
        voiceTranscript: "",
        voiceError: null,
      };
    case "voiceTranscriptUpdated":
      if (!state.voiceCallActive) {
        return state;
      }
      return {
        ...state,
        voiceTranscript: action.payload.text,
        voiceState: state.voiceState === "speaking" ? "speaking" : "recognizing",
      };
    case "voiceUserUtteranceFinal": {
      if (!state.voiceCallActive) {
        return state;
      }
      const { text, userMessageId, assistantMessageId } = action.payload;
      const hasUser = state.messages.some((m) => m.id === userMessageId);
      const hasAssistant = state.messages.some((m) => m.id === assistantMessageId);
      return {
        ...state,
        voiceTranscript: text,
        voiceState: "sending",
        messages: [
          ...state.messages,
          ...(hasUser
            ? []
            : [
                {
                  id: userMessageId,
                  role: "user" as const,
                  content: text,
                  status: "done" as const,
                },
              ]),
          ...(hasAssistant
            ? []
            : [
                {
                  id: assistantMessageId,
                  role: "assistant" as const,
                  content: "",
                  status: "sending" as const,
                },
              ]),
        ],
      };
    }
    case "voiceRecognized":
      return {
        ...state,
        voiceState: "recognizing",
      };
    case "voiceMessageSending":
      return {
        ...state,
        voiceState: "sending",
      };
    case "voicePlaybackStarted":
      if (!state.voiceCallActive) {
        return state;
      }
      return {
        ...state,
        voiceState: "speaking",
      };
    case "voicePlaybackFinished":
      return {
        ...state,
        voiceState: state.voiceCallActive ? "listening" : "idle",
      };
    case "voiceCallEnded":
    case "voiceInterruptRequested":
      return {
        ...state,
        voiceCallActive: false,
        voiceState: "idle",
        voiceTranscript: "",
      };
    case "voiceErrorOccurred":
      return {
        ...state,
        voiceCallActive: false,
        voiceState: "idle",
        voiceTranscript: "",
        voiceError: action.payload.message,
      };
    case "voiceCatalogUpdated":
      return {
        ...state,
        availableVoices: action.payload.voices,
        settings: action.payload.currentVoice
          ? { ...state.settings, voiceType: action.payload.currentVoice }
          : state.settings.voiceType || action.payload.voices.length === 0
            ? state.settings
            : { ...state.settings, voiceType: action.payload.voices[0] },
      };
    case "settingsChanged":
      return {
        ...state,
        settings: action.payload.settings,
      };
    case "vadBaselineUpdated":
      return {
        ...state,
        baselineVad: action.payload.baselineVad,
        emotionProfile: action.payload.emotionProfile ?? state.emotionProfile,
        currentAgentVad: action.payload.currentVad ?? state.currentAgentVad,
        currentRelationship: action.payload.relationship ?? state.currentRelationship,
      };
    case "affectTurnAppraised": {
      const { turnId, timestamp } = action.payload;
      const existing = state.affectHistory.find((item) => item.turnId === turnId);
      const record: AffectTurnRecord = {
        turnId,
        userText: action.payload.userText,
        createdAt: timestamp,
        schemaVersion: 2,
        phase: existing?.phase === "settled" ? "settled" : "appraised",
        userAffectVad: action.payload.userAffectVad,
        userWeight: action.payload.userWeight,
        relationship: action.payload.relationship,
        interpersonalCue: action.payload.interpersonalCue,
        responsePolicy: action.payload.responsePolicy,
        agentVadTarget: action.payload.agentVadTarget ?? undefined,
        actuationWeight: action.payload.actuationWeight,
        synthesisRule: action.payload.synthesisRule ?? existing?.synthesisRule,
        agentVadAfter: existing?.agentVadAfter,
        delta: existing?.delta,
        agentEmotion: existing?.agentEmotion,
        emotionScale: existing?.emotionScale,
      };
      return {
        ...state,
        currentRelationship: action.payload.relationship ?? state.currentRelationship,
        affectHistory: upsertAffectRecord(state.affectHistory, record),
      };
    }
    case "affectTurnSettled": {
      const { turnId, agentVadAfter, timestamp } = action.payload;
      const existing = state.affectHistory.find((item) => item.turnId === turnId);
      const baseForDelta = baseAgentVadForDelta(
        state.affectHistory,
        turnId,
        state.currentAgentVad,
        agentVadAfter,
      );
      const record: AffectTurnRecord = {
        turnId,
        userText: existing?.userText ?? "",
        createdAt: existing?.createdAt ?? timestamp,
        schemaVersion: existing?.schemaVersion ?? 2,
        phase: "settled",
        userAffectVad: existing?.userAffectVad ?? { v: 0, a: 0, d: 0 },
        userWeight: existing?.userWeight,
        relationship: existing?.relationship,
        interpersonalCue: existing?.interpersonalCue,
        responsePolicy: existing?.responsePolicy,
        agentVadTarget: existing?.agentVadTarget,
        actuationWeight: existing?.actuationWeight,
        agentVadAfter,
        delta: computeVadDelta(agentVadAfter, baseForDelta),
        agentEmotion: action.payload.agentEmotion,
        emotionScale: action.payload.emotionScale,
      };
      return {
        ...state,
        currentAgentVad: agentVadAfter,
        affectHistory: upsertAffectRecord(state.affectHistory, record),
      };
    }
    case "vadTurnEvaluated": {
      const { turnId, agentVadAfter, utteranceVad, timestamp } = action.payload;
      const baseForDelta = baseAgentVadForDelta(
        state.affectHistory,
        turnId,
        state.currentAgentVad,
        agentVadAfter,
      );
      const record: AffectTurnRecord = {
        turnId,
        userText: action.payload.userText,
        createdAt: timestamp,
        schemaVersion: 1,
        phase: "settled",
        userAffectVad: utteranceVad,
        agentVadAfter,
        delta: computeVadDelta(agentVadAfter, baseForDelta),
        agentEmotion: "neutral",
        emotionScale: 4,
      };
      return {
        ...state,
        currentAgentVad: agentVadAfter,
        affectHistory: upsertAffectRecord(state.affectHistory, record),
      };
    }
    case "historyHydrated":
      return {
        ...state,
        messages: mergeHistoryMessages(state.messages, action.payload.messages),
      };
    case "historyPrepended":
      return {
        ...state,
        messages: mergeHistoryMessages(state.messages, action.payload.messages),
      };
    case "chatCleared":
      return {
        ...initialChatState,
        settings: state.settings,
        connectionStatus: state.connectionStatus,
      };
    default:
      return state;
  }
}
