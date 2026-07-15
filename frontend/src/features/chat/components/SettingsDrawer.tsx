import { useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { cn } from "@/lib/utils";
import { useScrollEdgeFade } from "../hooks/useScrollEdgeFade";
import type { ChatSettings } from "../types";
import { HUOSHAN_TTS_VOICE_META, HUOSHAN_TTS_VOICE_OPTIONS } from "../ttsVoices";
import { SettingsVoicePage } from "./SettingsVoicePage";
import "./settings-ios.css";

interface SettingsDrawerProps {
  open: boolean;
  settings: ChatSettings;
  onClose: () => void;
  onSettingsChange: (next: ChatSettings) => void;
  onRequestClearUserData: () => void;
}

type SettingsPage = "root" | "voice";

interface InlineSegmentProps<T extends string> {
  value: T;
  options: ReadonlyArray<{ value: T; label: string }>;
  onChange: (value: T) => void;
  ariaLabel: string;
}

function InlineSegment<T extends string>({ value, options, onChange, ariaLabel }: InlineSegmentProps<T>) {
  return (
    <ToggleGroup
      type="single"
      value={value}
      onValueChange={(next) => {
        if (next) {
          onChange(next as T);
        }
      }}
      className="ios-settings-segment"
      aria-label={ariaLabel}
    >
      {options.map((option) => (
        <ToggleGroupItem
          key={option.value}
          value={option.value}
          className="ios-settings-segment__btn flex-1 rounded-[0.5rem] border-0 bg-transparent px-2 py-[0.4375rem] text-[0.9375rem] font-medium shadow-none hover:bg-transparent data-[state=on]:bg-[var(--apple-cell-bg)] data-[state=on]:text-[var(--apple-accent)] data-[state=on]:shadow-[0_1px_3px_rgb(0_0_0_/_10%),0_1px_0_rgb(255_255_255_/_70%)_inset]"
        >
          {option.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

export function SettingsDrawer({
  open,
  settings,
  onClose,
  onSettingsChange,
  onRequestClearUserData,
}: SettingsDrawerProps) {
  const isMobile = useMediaQuery("(max-width: 767px)");
  const rootScrollRef = useRef<HTMLDivElement>(null);
  const voiceScrollRef = useRef<HTMLDivElement>(null);
  const [page, setPage] = useState<SettingsPage>("root");

  const activeScrollRef = page === "root" ? rootScrollRef : voiceScrollRef;
  const { fadeTop, fadeBottom, onScroll } = useScrollEdgeFade(activeScrollRef, open);

  const update = <K extends keyof ChatSettings>(key: K, value: ChatSettings[K]) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  const currentVoiceMeta = HUOSHAN_TTS_VOICE_META[settings.voiceType];
  const currentVoiceDisplay = currentVoiceMeta?.label || settings.voiceType;

  const voiceGroups = useMemo(() => {
    const grouped = new Map<string, Array<{ value: string; label: string }>>();
    const voices = Array.from(
      new Set([settings.voiceType, ...HUOSHAN_TTS_VOICE_OPTIONS.map((item) => item.value)].map((item) => item.trim()).filter(Boolean)),
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

  const resetNavigation = () => {
    setPage("root");
  };

  const handleSheetOpenChange = (next: boolean) => {
    if (next) {
      return;
    }
    const active = document.activeElement;
    if (active instanceof HTMLElement) {
      active.blur();
    }
    resetNavigation();
    onClose();
  };

  return (
    <Sheet open={open} onOpenChange={handleSheetOpenChange}>
      <SheetContent
        role="dialog"
        aria-label={page === "voice" ? "音色设置" : "设置面板"}
        side={isMobile ? "bottom" : "center"}
        data-appearance={settings.appearance}
        className={cn(
          "ios-settings-root ios-settings-sheet",
          isMobile ? "ios-settings-sheet--bottom" : "ios-settings-sheet--center",
        )}
        overlayClassName={cn("ios-settings-overlay", settings.appearance === "dark" && "ios-settings-overlay--dark")}
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          const fallback = document.body;
          if (fallback instanceof HTMLElement) {
            fallback.focus({ preventScroll: true });
          }
        }}
      >
        <div className="ios-settings-sheet__panel">
          {isMobile ? <div className="ios-settings-drag-handle" aria-hidden /> : null}

          {page === "root" ? (
            <SheetHeader className="ios-settings-header ios-settings-header--glass">
              <SheetTitle>设置</SheetTitle>
              <SheetDescription>调整语音与显示偏好</SheetDescription>
            </SheetHeader>
          ) : (
            <header className="ios-settings-header ios-settings-header--glass ios-settings-header--nav">
              <Button
                type="button"
                variant="ghost"
                className="ios-settings-back h-auto rounded-none px-0 py-0 shadow-none hover:bg-transparent"
                onClick={() => setPage("root")}
              >
                <ChevronLeft className="h-4 w-4 shrink-0" aria-hidden />
                <span>设置</span>
              </Button>
              <h2 className="ios-settings-header__title">音色</h2>
              <span className="ios-settings-header__spacer" aria-hidden />
            </header>
          )}

          <div className="ios-settings-nav">
            <div className={cn("ios-settings-nav__track", page === "voice" && "ios-settings-nav__track--voice")}>
              <div className="ios-settings-nav__page" aria-hidden={page !== "root"}>
                <div className="ios-settings-scroll-chrome">
                  <div
                    className={cn("ios-settings-scroll-edge ios-settings-scroll-edge--top", page === "root" && fadeTop && "is-visible")}
                    aria-hidden
                  />
                  <div
                    ref={rootScrollRef}
                    className="ios-settings-body"
                    onScroll={page === "root" ? onScroll : undefined}
                    aria-hidden={page !== "root"}
                  >
                    <section className="ios-settings-group" aria-labelledby="settings-voice-heading">
                      <h3 id="settings-voice-heading" className="ios-settings-group__label">
                        语音
                      </h3>
                      <div className="ios-settings-list">
                        <div className="ios-settings-row">
                          <Label htmlFor="voice-enabled" className="ios-settings-row__label">
                            语音总开关
                          </Label>
                          <Switch
                            id="voice-enabled"
                            className="ios-settings-switch"
                            checked={settings.voiceEnabled}
                            onCheckedChange={(checked) => update("voiceEnabled", checked)}
                          />
                        </div>
                        <div className="ios-settings-row">
                          <Label htmlFor="auto-play-voice" className="ios-settings-row__label">
                            自动播报
                          </Label>
                          <Switch
                            id="auto-play-voice"
                            className="ios-settings-switch"
                            aria-label="自动播报"
                            checked={settings.autoPlayVoice}
                            onCheckedChange={(checked) => update("autoPlayVoice", checked)}
                          />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          className="ios-settings-row ios-settings-row--disclosure h-auto w-full justify-between rounded-none px-0 py-0 font-normal shadow-none hover:bg-transparent"
                          onClick={() => setPage("voice")}
                        >
                          <span className="ios-settings-row__label">音色</span>
                          <span className="ios-settings-row__value truncate">{currentVoiceDisplay}</span>
                          <ChevronRight className="ios-settings-row__chevron h-4 w-4 shrink-0" aria-hidden />
                        </Button>
                      </div>
                    </section>

                    <section className="ios-settings-group" aria-labelledby="settings-display-heading">
                      <h3 id="settings-display-heading" className="ios-settings-group__label">
                        显示
                      </h3>
                      <div className="ios-settings-list">
                        <div className="ios-settings-row">
                          <Label htmlFor="appearance-dark" className="ios-settings-row__label">
                            深色外观
                          </Label>
                          <Switch
                            id="appearance-dark"
                            className="ios-settings-switch"
                            checked={settings.appearance === "dark"}
                            onCheckedChange={(checked) => update("appearance", checked ? "dark" : "light")}
                          />
                        </div>
                        <div className="ios-settings-row ios-settings-row--stacked">
                          <Label className="ios-settings-row__label">字体大小</Label>
                          <InlineSegment
                            ariaLabel="字体大小"
                            value={settings.fontSize}
                            options={[
                              { value: "normal", label: "标准" },
                              { value: "large", label: "大号" },
                            ]}
                            onChange={(value) => update("fontSize", value)}
                          />
                        </div>
                        <div className="ios-settings-row ios-settings-row--stacked">
                          <Label className="ios-settings-row__label">动效强度</Label>
                          <InlineSegment
                            ariaLabel="动效强度"
                            value={settings.motion}
                            options={[
                              { value: "normal", label: "标准" },
                              { value: "reduced", label: "减弱" },
                            ]}
                            onChange={(value) => update("motion", value)}
                          />
                        </div>
                      </div>
                    </section>

                    <section className="ios-settings-group" aria-labelledby="settings-data-heading">
                      <h3 id="settings-data-heading" className="ios-settings-group__label ios-settings-group__label--danger">
                        数据
                      </h3>
                      <div className="ios-settings-list">
                        <Button
                          type="button"
                          variant="ghost"
                          className="ios-settings-row ios-settings-row--destructive h-auto w-full rounded-none px-0 py-0 font-normal shadow-none hover:bg-transparent"
                          onClick={onRequestClearUserData}
                        >
                          清空用户数据
                        </Button>
                      </div>
                      <p className="ios-settings-hint ios-settings-hint--footer">
                        删除当前用户在本机的对话、设置与服务端记忆，并生成新用户身份后刷新页面。此操作不可恢复。
                      </p>
                    </section>
                  </div>
                  <div
                    className={cn(
                      "ios-settings-scroll-edge ios-settings-scroll-edge--bottom",
                      page === "root" && fadeBottom && "is-visible",
                    )}
                    aria-hidden
                  />
                </div>
              </div>

              <div className="ios-settings-nav__page" aria-hidden={page !== "voice"}>
                <div className="ios-settings-scroll-chrome">
                  <div
                    className={cn("ios-settings-scroll-edge ios-settings-scroll-edge--top", page === "voice" && fadeTop && "is-visible")}
                    aria-hidden
                  />
                  <div
                    ref={voiceScrollRef}
                    className="ios-settings-body"
                    onScroll={page === "voice" ? onScroll : undefined}
                    aria-hidden={page !== "voice"}
                  >
                    <SettingsVoicePage
                      voiceGroups={voiceGroups}
                      selectedVoice={settings.voiceType}
                      onSelectVoice={(voice) => {
                        update("voiceType", voice);
                        setPage("root");
                      }}
                    />
                  </div>
                  <div
                    className={cn(
                      "ios-settings-scroll-edge ios-settings-scroll-edge--bottom",
                      page === "voice" && fadeBottom && "is-visible",
                    )}
                    aria-hidden
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
