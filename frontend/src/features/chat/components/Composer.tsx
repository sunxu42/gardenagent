import { FormEvent, KeyboardEvent, useRef } from "react";
import { ArrowUp, Mic, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAutosizeChatTextarea } from "../hooks/useAutosizeChatTextarea";
import type { VoiceState } from "../types";
import { cn } from "@/lib/utils";

interface ComposerProps {
  value: string;
  voiceError: string | null;
  onChange: (value: string) => void;
  onSend: () => void;
  voiceCallActive: boolean;
  voiceState: VoiceState;
  onStartVoiceCall: () => void;
  onEndVoiceCall: () => void;
}

export function Composer({
  value,
  voiceError,
  onChange,
  onSend,
  voiceCallActive,
  voiceState,
  onStartVoiceCall,
  onEndVoiceCall,
}: ComposerProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  useAutosizeChatTextarea(inputRef, value);

  const inCall = voiceCallActive;
  const hasText = value.trim().length > 0;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!hasText) {
      return;
    }
    onSend();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) {
      return;
    }
    event.preventDefault();
    if (!hasText) {
      return;
    }
    event.currentTarget.form?.requestSubmit();
  };

  if (inCall) {
    return (
      <div className="flex justify-center py-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className={cn(
            "chat-ios-voice-end h-auto w-auto rounded-full",
            voiceState === "speaking" && "chat-ios-voice-end--speaking",
          )}
          aria-label="结束通话"
          onClick={onEndVoiceCall}
        >
          <Phone className="h-6 w-6" strokeWidth={2} />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full">
      {voiceError ? (
        <p className="mb-1.5 text-xs text-[var(--ios-red)]" role="alert">
          {voiceError}
        </p>
      ) : null}
      <form onSubmit={handleSubmit} className="chat-ios-composer">
        <Label htmlFor="chat-input" className="sr-only">
          消息输入框
        </Label>
        <div className="chat-ios-composer__field liquid-glass">
          <Textarea
            id="chat-input"
            ref={inputRef}
            rows={1}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息"
            className="composer-textarea resize-none break-words border-0 bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          {hasText ? (
            <Button
              type="submit"
              variant="ghost"
              size="icon"
              className="chat-ios-send-btn h-auto w-auto shrink-0 rounded-full"
              aria-label="发送"
            >
              <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
            </Button>
          ) : (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="chat-ios-action-btn h-auto w-auto shrink-0 rounded-full"
              aria-label="语音通话"
              onClick={onStartVoiceCall}
            >
              <Mic className="h-5 w-5" strokeWidth={2} />
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
