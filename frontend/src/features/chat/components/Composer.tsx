import { FormEvent, KeyboardEvent, useRef } from "react";
import { Phone, SendHorizontal } from "lucide-react";
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
      <div className="flex justify-center py-1">
        <Button
          type="button"
          className={cn(
            "h-14 w-14 rounded-full bg-red-500 p-0 text-white hover:bg-red-600",
            voiceState === "speaking" && "ring-2 ring-red-300/80"
          )}
          aria-label="结束通话"
          onClick={onEndVoiceCall}
        >
          <Phone className="h-6 w-6" />
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="m-0">
      {voiceError ? (
        <p className="mb-1.5 text-xs text-destructive" role="alert">
          {voiceError}
        </p>
      ) : null}
      <Label htmlFor="chat-input" className="sr-only">
        消息输入框
      </Label>
      <div className="grid grid-cols-[1fr_auto] items-end gap-1.5 md:gap-2">
        <Textarea
          id="chat-input"
          ref={inputRef}
          rows={1}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息"
          className="composer-textarea min-h-10 resize-none break-words md:min-h-11 md:rounded-xl md:px-3.5 md:py-2.5 md:placeholder:text-muted-foreground/80"
        />
        {hasText ? (
          <Button
            type="submit"
            size="icon"
            className="h-10 w-10 shrink-0 cursor-pointer transition-colors duration-200 md:h-11 md:w-11"
            aria-label="发送"
          >
            <SendHorizontal className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            type="button"
            size="icon"
            variant="outline"
            className="h-10 w-10 shrink-0 cursor-pointer transition-colors duration-200 hover:bg-background md:h-11 md:w-11"
            aria-label="语音通话"
            onClick={onStartVoiceCall}
          >
            <Phone className="h-5 w-5 text-primary" />
          </Button>
        )}
      </div>
    </form>
  );
}
