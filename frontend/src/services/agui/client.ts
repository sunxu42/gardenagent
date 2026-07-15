import type { ChatAction } from "../../features/chat/types";
import { mapAguiEvent, parseAguiEnvelope, type AguiEvent } from "./mapAguiEvent";

export interface AguiClientOptions {
  onAction: (action: ChatAction) => void;
  getAssistantMessageId: () => string | null;
  setAssistantMessageId: (id: string | null) => void;
  sendEnvelope?: (payload: Record<string, unknown>) => boolean;
}

export function createAguiClient(options: AguiClientOptions) {
  const handleEnvelope = (raw: Record<string, unknown>, agentName?: string) => {
    const event = parseAguiEnvelope(raw);
    if (!event) {
      return false;
    }
    const action = mapAguiEvent(event, options.getAssistantMessageId(), agentName);
    if (!action) {
      return true;
    }
    options.onAction(action);
    if (action.type === "aguiRunFinished" || action.type === "aguiRunError") {
      options.setAssistantMessageId(null);
    }
    return true;
  };

  const handleEvent = (event: AguiEvent, agentName?: string) => {
    const action = mapAguiEvent(event, options.getAssistantMessageId(), agentName);
    if (!action) {
      return;
    }
    options.onAction(action);
    if (action.type === "aguiRunFinished" || action.type === "aguiRunError") {
      options.setAssistantMessageId(null);
    }
  };

  const sendUiAction = (payload: {
    runId: string;
    surfaceId: string;
    messageId: string;
    action: {
      name: string;
      context?: Record<string, unknown>;
      sourceComponentId?: string;
      dataModel?: Record<string, unknown>;
    };
  }): boolean => {
    if (!options.sendEnvelope) {
      return false;
    }
    return options.sendEnvelope({
      channel: "agui",
      event: {
        type: "UI_ACTION",
        runId: payload.runId,
        surfaceId: payload.surfaceId,
        messageId: payload.messageId,
        action: payload.action,
      },
    });
  };

  return { handleEnvelope, handleEvent, sendUiAction };
}
