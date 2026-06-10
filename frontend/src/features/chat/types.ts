import type { LogEntry } from "../logs/logTypes";

export type MessageRole = "user" | "assistant";

export type MessageStatus = "sending" | "streaming" | "done";

export type ConnectionStatus = "online" | "offline";

export type VoiceState = "idle" | "listening" | "recognizing" | "sending" | "agentThinking" | "speaking";
export type ThemeName = "mint-cute" | "pink-blossom" | "gray-mist" | "orange-sunrise";

export interface ChatSettings {
  voiceEnabled: boolean;
  autoPlayVoice: boolean;
  voiceType: string;
  fontSize: "normal" | "large";
  motion: "normal" | "reduced";
  theme: ThemeName;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  /** 助手展示名（由 WebSocket agent_name 注入） */
  authorLabel?: string;
  /** IndexedDB 排序与分页用（新消息在首次持久化时写入） */
  createdAt?: number;
}

export interface VadPoint {
  v: number;
  a: number;
  d: number;
}

export type AffectPhase = "appraised" | "settled";

export interface RelationshipSnapshot {
  trust: number;
  warmth: number;
  stage: string;
  trustDelta?: number;
  warmthDelta?: number;
  relWeight?: number;
}

export interface RelationshipBaseline {
  trust: number;
  warmth: number;
}

export interface EmotionProfile {
  userVadBaseline: VadPoint;
  agentVadBaseline: VadPoint;
  relationshipBaseline: RelationshipBaseline;
  userAffect: { perTurnOnly: boolean };
  agentVad: { perTurnAlpha: number; perTurnBeta: number; timeTauSec: number };
  relationship: { perTurnAlpha: number; timeTauSec: number };
}

export interface StrategyTagsSnapshot {
  mode: string;
  voiceStyle: string;
  length: string;
  llmGuideline: string;
  ttsProfile: string;
}

export interface ResponsePolicySnapshot {
  empathyMode: string;
  stance: string;
  repairAction: string;
  directiveness: number;
}

export interface AffectTurnRecord {
  turnId: string;
  userText: string;
  createdAt: number;
  schemaVersion: 1 | 2;
  phase: AffectPhase;
  userAffectVad: VadPoint;
  userWeight?: number;
  relationship?: RelationshipSnapshot;
  interpersonalCue?: string;
  responsePolicy?: ResponsePolicySnapshot;
  agentVadTarget?: VadPoint;
  actuationWeight?: number;
  agentVadAfter?: VadPoint;
  delta?: VadPoint;
  agentEmotion?: string;
  emotionScale?: number;
  synthesisRule?: string;
  strategyTags?: StrategyTagsSnapshot;
}

export interface ChatState {
  messages: ChatMessage[];
  inputValue: string;
  connectionStatus: ConnectionStatus;
  availableVoices: string[];
  /** 是否处于语音通话 footer（与文字聊天的 TTS/ASR 回显解耦） */
  voiceCallActive: boolean;
  voiceState: VoiceState;
  voiceTranscript: string;
  voiceError: string | null;
  settings: ChatSettings;
  affectHistory: AffectTurnRecord[];
  currentAgentVad: VadPoint | null;
  baselineVad: VadPoint | null;
  emotionProfile: EmotionProfile | null;
  currentRelationship: RelationshipSnapshot | null;
  logEntries: LogEntry[];
}

export type ChatAction =
  | { type: "inputChanged"; payload: { value: string } }
  | { type: "messageQueued"; payload: { id: string; role: MessageRole; content: string } }
  | { type: "messageStreamStart"; payload: { id: string; agentName?: string } }
  | {
      type: "messageStreaming";
      payload: { id: string; content: string; agentName?: string };
    }
  | { type: "messageDone"; payload: { id: string } }
  | { type: "connectionChanged"; payload: { status: ConnectionStatus } }
  | { type: "voiceListeningStarted" }
  | { type: "voiceTranscriptUpdated"; payload: { text: string } }
  | {
      type: "voiceUserUtteranceFinal";
      payload: { text: string; userMessageId: string; assistantMessageId: string };
    }
  | { type: "voiceRecognized" }
  | { type: "voiceMessageSending" }
  | { type: "voicePlaybackStarted" }
  | { type: "voicePlaybackFinished" }
  | { type: "voiceCallEnded" }
  | { type: "voiceInterruptRequested" }
  | { type: "voiceErrorOccurred"; payload: { message: string } }
  | { type: "voiceCatalogUpdated"; payload: { voices: string[]; currentVoice?: string } }
  | {
      type: "vadBaselineUpdated";
      payload: {
        baselineVad: VadPoint | null;
        currentVad?: VadPoint | null;
        relationship?: RelationshipSnapshot | null;
        emotionProfile?: EmotionProfile | null;
      };
    }
  | { type: "settingsChanged"; payload: { settings: ChatSettings } }
  | {
      type: "affectTurnAppraised";
      payload: {
        turnId: string;
        userText: string;
        timestamp: number;
        userAffectVad: VadPoint;
        userWeight?: number;
        relationship?: RelationshipSnapshot;
        interpersonalCue?: string;
        responsePolicy?: ResponsePolicySnapshot;
        agentVadTarget?: VadPoint | null;
        actuationWeight?: number;
        synthesisRule?: string;
        strategyTags?: StrategyTagsSnapshot;
      };
    }
  | {
      type: "affectTurnSettled";
      payload: {
        turnId: string;
        agentVadAfter: VadPoint;
        agentEmotion: string;
        emotionScale: number;
        timestamp: number;
      };
    }
  | {
      type: "vadTurnEvaluated";
      payload: {
        turnId: string;
        userText: string;
        utteranceVad: VadPoint;
        agentVadAfter: VadPoint;
        timestamp: number;
      };
    }
  | { type: "historyHydrated"; payload: { messages: ChatMessage[] } }
  | { type: "historyPrepended"; payload: { messages: ChatMessage[] } }
  | { type: "logEntryReceived"; payload: { entry: LogEntry } }
  | { type: "clearLogs"; payload?: { previousCount?: number } }
  | { type: "chatCleared" };
