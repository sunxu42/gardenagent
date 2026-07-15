import { Check } from "lucide-react";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import { HUOSHAN_TTS_VOICE_META } from "../ttsVoices";

export interface VoiceGroup {
  scene: string;
  items: Array<{ value: string; label: string }>;
}

interface SettingsVoicePageProps {
  voiceGroups: VoiceGroup[];
  selectedVoice: string;
  onSelectVoice: (voice: string) => void;
}

export function SettingsVoicePage({ voiceGroups, selectedVoice, onSelectVoice }: SettingsVoicePageProps) {
  const selectedMeta = HUOSHAN_TTS_VOICE_META[selectedVoice];

  return (
    <>
      {voiceGroups.map((group) => (
        <section key={group.scene} className="ios-settings-group" aria-labelledby={`voice-scene-${group.scene}`}>
          <h3 id={`voice-scene-${group.scene}`} className="ios-settings-group__label">
            {group.scene}
          </h3>
          <RadioGroup
            value={selectedVoice}
            onValueChange={onSelectVoice}
            className="ios-settings-list gap-0"
          >
            {group.items.map((voice) => {
              const selected = selectedVoice === voice.value;
              const itemId = `voice-${voice.value}`;
              return (
                <div key={voice.value} className="relative">
                  <RadioGroupItem value={voice.value} id={itemId} className="sr-only" />
                  <Label
                    htmlFor={itemId}
                    className={cn(
                      "ios-settings-row ios-settings-row--option",
                      selected && "ios-settings-row--option-active",
                    )}
                  >
                    <span className="truncate">{voice.label}</span>
                    {selected ? (
                      <Check className="h-4 w-4 shrink-0 text-[var(--apple-accent)]" aria-hidden />
                    ) : null}
                  </Label>
                </div>
              );
            })}
          </RadioGroup>
        </section>
      ))}
      {selectedMeta?.description ? (
        <p className="ios-settings-hint ios-settings-hint--footer">{selectedMeta.description}</p>
      ) : null}
    </>
  );
}
