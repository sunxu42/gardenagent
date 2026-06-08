import { useMemo, useState } from "react";
import { Label } from "@/components/ui/label";
import { Check } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import type { ChatSettings } from "../types";
import { HUOSHAN_TTS_VOICE_META, HUOSHAN_TTS_VOICE_OPTIONS } from "../ttsVoices";

interface SettingsDrawerProps {
  open: boolean;
  settings: ChatSettings;
  onClose: () => void;
  onSettingsChange: (next: ChatSettings) => void;
  onRequestClearUserData: () => void;
}

const themeOptions: Array<{
  value: ChatSettings["theme"];
  label: string;
  previewClassName: string;
  chips: {
    primary: string;
    secondary: string;
    accent: string;
  };
  checkBadgeClassName: string;
}> = [
  {
    value: "mint-cute",
    label: "浅绿色",
    previewClassName: "from-emerald-100 via-emerald-50 to-white",
    chips: {
      primary: "bg-emerald-500",
      secondary: "bg-emerald-200",
      accent: "bg-orange-300",
    },
    checkBadgeClassName: "bg-emerald-500 text-white",
  },
  {
    value: "pink-blossom",
    label: "粉色",
    previewClassName: "from-pink-100 via-rose-50 to-white",
    chips: {
      primary: "bg-pink-500",
      secondary: "bg-pink-200",
      accent: "bg-rose-300",
    },
    checkBadgeClassName: "bg-pink-500 text-white",
  },
  {
    value: "gray-mist",
    label: "灰色",
    previewClassName: "from-slate-200 via-slate-100 to-white",
    chips: {
      primary: "bg-slate-500",
      secondary: "bg-slate-300",
      accent: "bg-zinc-400",
    },
    checkBadgeClassName: "bg-slate-500 text-white",
  },
  {
    value: "orange-sunrise",
    label: "橙色",
    previewClassName: "from-orange-100 via-amber-50 to-white",
    chips: {
      primary: "bg-orange-500",
      secondary: "bg-orange-200",
      accent: "bg-amber-300",
    },
    checkBadgeClassName: "bg-orange-500 text-white",
  },
];

export function SettingsDrawer({
  open,
  settings,
  onClose,
  onSettingsChange,
  onRequestClearUserData,
}: SettingsDrawerProps) {
  const [expandedScenes, setExpandedScenes] = useState<Record<string, boolean>>({});
  const [voiceMenuOpen, setVoiceMenuOpen] = useState(false);
  const update = <K extends keyof ChatSettings>(key: K, value: ChatSettings[K]) => {
    onSettingsChange({ ...settings, [key]: value });
  };
  const currentVoiceMeta = HUOSHAN_TTS_VOICE_META[settings.voiceType];
  const currentVoiceDisplay = currentVoiceMeta?.label || settings.voiceType;
  const voiceGroups = useMemo(() => {
    const grouped = new Map<string, Array<{ value: string; label: string }>>();
    const voices = Array.from(
      new Set([settings.voiceType, ...HUOSHAN_TTS_VOICE_OPTIONS.map((item) => item.value)].map((item) => item.trim()).filter(Boolean))
    );
    voices.forEach((voice) => {
      const scene = HUOSHAN_TTS_VOICE_OPTIONS.find((item) => item.value === voice)?.scene || "未分类";
      const label = HUOSHAN_TTS_VOICE_META[voice]?.label || voice;
      if (!grouped.has(scene)) {
        grouped.set(scene, []);
      }
      grouped.get(scene)!.push({ value: voice, label });
    });
    return Array.from(grouped.entries()).map(([scene, items]) => ({ scene, items }));
  }, [settings.voiceType]);

  const toggleScene = (scene: string) => {
    setExpandedScenes((prev) => ({ ...prev, [scene]: !prev[scene] }));
  };
  const handleSheetOpenChange = (next: boolean) => {
    if (next) return;
    const active = document.activeElement;
    if (active instanceof HTMLElement) {
      active.blur();
    }
    onClose();
  };

  return (
    <Sheet open={open} onOpenChange={handleSheetOpenChange}>
      <SheetContent
        role="dialog"
        aria-label="设置面板"
        className="md:max-w-md"
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          const fallback = document.body;
          if (fallback instanceof HTMLElement) {
            fallback.focus({ preventScroll: true });
          }
        }}
      >
        <SheetHeader>
          <SheetTitle>设置</SheetTitle>
          <SheetDescription>在这里调整语音与显示偏好。</SheetDescription>
        </SheetHeader>

        <section className="mt-6 grid gap-2">
          <h3 className="mb-2 text-sm font-semibold">语音</h3>
          <div className="flex items-center justify-between">
            <Label htmlFor="voice-enabled">语音总开关</Label>
            <Switch
              id="voice-enabled"
              checked={settings.voiceEnabled}
              onCheckedChange={(checked) => update("voiceEnabled", checked)}
            />
          </div>
          <div className="mt-3 flex items-center justify-between">
            <Label htmlFor="auto-play-voice">自动播报</Label>
            <Switch
              id="auto-play-voice"
              aria-label="自动播报"
              checked={settings.autoPlayVoice}
              onCheckedChange={(checked) => update("autoPlayVoice", checked)}
            />
          </div>
          <div className="mt-3">
            <Label className="mb-2 block">音色</Label>
            <button
              type="button"
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              aria-expanded={voiceMenuOpen}
              onClick={() => setVoiceMenuOpen((prev) => !prev)}
            >
              <span className="truncate">{currentVoiceDisplay || "请选择音色"}</span>
              <span className="ml-2 text-xs text-muted-foreground">{voiceMenuOpen ? "▴" : "▾"}</span>
            </button>
            {voiceMenuOpen ? (
              <div className="mt-2 max-h-72 overflow-auto rounded-md border border-input bg-popover p-1">
                {voiceGroups.map((group) => {
                  const isExpanded = !!expandedScenes[group.scene];
                  return (
                    <div key={group.scene} className="py-1">
                      <button
                        type="button"
                        className="flex w-full items-center justify-between rounded px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        aria-expanded={isExpanded}
                        onClick={() => toggleScene(group.scene)}
                      >
                        <span>{group.scene}</span>
                        <span>{isExpanded ? "▾" : "▸"}</span>
                      </button>
                      {isExpanded ? (
                        <div className="mt-1 space-y-1 pl-2">
                          {group.items.map((voice) => (
                            <button
                              key={voice.value}
                              type="button"
                              className={`block w-full rounded px-2 py-1 text-left text-sm hover:bg-accent ${
                                settings.voiceType === voice.value ? "bg-accent text-accent-foreground" : ""
                              }`}
                              onClick={() => {
                                update("voiceType", voice.value);
                                setVoiceMenuOpen(false);
                              }}
                            >
                              {voice.label}
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : null}
            {currentVoiceMeta?.description ? (
              <p className="mt-2 text-xs text-muted-foreground">{currentVoiceMeta.description}</p>
            ) : null}
          </div>
        </section>

        <section className="mt-6 grid gap-2">
          <h3 className="mb-2 text-sm font-semibold text-destructive">数据</h3>
          <p className="text-xs text-muted-foreground">
            删除当前用户在本机的对话、设置与服务端记忆，并生成新用户身份后刷新页面。此操作不可恢复。
          </p>
          <button
            type="button"
            className="mt-1 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-left text-sm font-medium text-destructive transition hover:bg-destructive/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
            onClick={onRequestClearUserData}
          >
            清空用户数据
          </button>
        </section>

        <section className="mt-6 grid gap-2">
          <h3 className="mb-2 text-sm font-semibold">显示</h3>
          <div>
            <Label className="mb-2 block">主题色</Label>
            <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="主题色">
              {themeOptions.map((option) => {
                const selected = settings.theme === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-label={option.label}
                    aria-checked={selected}
                    onClick={() => update("theme", option.value)}
                    className={`relative rounded-md border p-2 text-left transition ${
                      selected ? "border-primary ring-2 ring-primary/30" : "border-input hover:border-primary/50"
                    }`}
                  >
                    {selected ? (
                      <span
                        className={`absolute right-1.5 top-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full ${option.checkBadgeClassName}`}
                      >
                        <Check className="h-3 w-3" />
                      </span>
                    ) : null}
                    <div className={`mb-2 h-8 rounded bg-gradient-to-r ${option.previewClassName}`} />
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{option.label}</span>
                      <span className="flex items-center gap-1" aria-hidden="true">
                        <span className={`h-2.5 w-2.5 rounded-full ${option.chips.primary}`} />
                        <span className={`h-2.5 w-2.5 rounded-full ${option.chips.secondary}`} />
                        <span className={`h-2.5 w-2.5 rounded-full ${option.chips.accent}`} />
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <Label className="mb-2 block">字体大小</Label>
            <Select
              value={settings.fontSize}
              onValueChange={(value) => update("fontSize", value as ChatSettings["fontSize"])}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">标准</SelectItem>
                <SelectItem value="large">大号</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="mt-3">
            <Label className="mb-2 block">动效强度</Label>
            <Select
              value={settings.motion}
              onValueChange={(value) => update("motion", value as ChatSettings["motion"])}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">标准</SelectItem>
                <SelectItem value="reduced">减弱</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </section>
      </SheetContent>
    </Sheet>
  );
}
