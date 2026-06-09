import { BookOpen, ChevronRight, ListOrdered, X } from "lucide-react";
import type { AffectTurnRecord, EmotionProfile, RelationshipSnapshot, VadPoint } from "../types";
import { AffectBaselineDecayGuide } from "./affect/AffectBaselineDecayGuide";
import { AffectFlowDiagram } from "./affect/AffectFlowDiagram";
import { AffectRecordFieldGuide } from "./affect/AffectRecordFieldGuide";
import { AffectRoundSnapshotHero } from "./affect/AffectRoundSnapshotHero";
import {
  GuideCollapsibleSection,
  GuidePrioritySection,
} from "./affect/GuideSection";
import { VadDimensionGuide } from "./affect/VadDimensionGuide";

interface AffectGuidePanelProps {
  open: boolean;
  onClose: () => void;
  focusedRecord?: AffectTurnRecord | null;
  focusedRoundLabel?: string | null;
  currentRelationship?: RelationshipSnapshot | null;
  emotionProfile?: EmotionProfile | null;
  agentBaselineVad?: VadPoint | null;
}

const READ_ORDER = ["本轮快照", "记录字段", "处理流程", "V/A/D 基础", "Baseline 进阶"];

export function AffectGuidePanel({
  open,
  onClose,
  focusedRecord,
  focusedRoundLabel,
  currentRelationship,
  emotionProfile,
  agentBaselineVad,
}: AffectGuidePanelProps) {
  const snapshot = focusedRecord ?? null;
  const rel = snapshot?.relationship ?? currentRelationship ?? null;

  return (
    <aside
      id="affect-guide-drawer"
      className={`affect-guide-drawer flex min-h-0 shrink-0 flex-col overflow-hidden ${open ? "affect-guide-drawer--open" : ""}`}
      aria-hidden={!open}
      data-open={open ? "true" : "false"}
    >
      {open ? (
        <>
          <header className="affect-rail-header shrink-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-muted/50 text-muted-foreground">
                    <BookOpen className="h-3.5 w-3.5" aria-hidden />
                  </span>
                  情绪模块说明
                </h3>
                <p className="mt-1.5 pl-8 text-[11px] leading-relaxed text-muted-foreground/90">
                  按重要程度阅读：先看本轮结果，再对照记录栏，最后了解机制。
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="shrink-0 cursor-pointer rounded-lg p-2 text-muted-foreground transition-colors duration-200 hover:bg-muted/80 hover:text-foreground"
                aria-label="收起说明"
                title="收起"
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            </div>
          </header>

          <div className="affect-panel-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-6 pt-3">
            <nav
              className="mb-4 flex flex-wrap items-center gap-1.5 rounded-lg border border-border/30 bg-muted/10 px-2.5 py-2"
              aria-label="阅读顺序"
            >
              <ListOrdered className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />
              {READ_ORDER.map((label, i) => (
                <span key={label} className="inline-flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  {i > 0 ? <span className="text-border">·</span> : null}
                  <span className="font-medium tabular-nums text-foreground/80">{i + 1}</span>
                  {label}
                </span>
              ))}
            </nav>

            <div className="space-y-4">
              <GuidePrioritySection
                priority={1}
                variant="hero"
                title="本轮情绪快照"
                description="最重要：选中某轮后，快速看懂双方情绪与回应态度。"
              >
                <AffectRoundSnapshotHero
                  snapshot={snapshot}
                  focusedRoundLabel={focusedRoundLabel}
                  relationship={rel}
                />
              </GuidePrioritySection>

              <GuidePrioritySection
                priority={2}
                title="读懂左侧记录"
                description="对照记录栏各字段，理解每列数字代表什么。"
              >
                <AffectRecordFieldGuide />
              </GuidePrioritySection>

              <GuidePrioritySection
                priority={3}
                title="每轮怎么处理"
                description="你的话如何影响助手的语气与态度（业务主链路）。"
              >
                <AffectFlowDiagram />
              </GuidePrioritySection>

              <GuideCollapsibleSection
                priority={4}
                title="V/A/D 三个维度"
                description="愉悦度、能量感、掌控感 — 所有数值的共同坐标系。"
              >
                <div className="rounded-lg border border-border/30 bg-muted/10 p-3">
                  <VadDimensionGuide />
                </div>
              </GuideCollapsibleSection>

              <GuideCollapsibleSection
                priority={5}
                title="Baseline 与衰减"
                description="默认参考点与长期回落规律（进阶，不影响日常阅读记录）。"
              >
                <AffectBaselineDecayGuide
                  profile={emotionProfile}
                  agentBaselineFallback={agentBaselineVad}
                />
              </GuideCollapsibleSection>
            </div>
          </div>
        </>
      ) : null}
    </aside>
  );
}

export function AffectGuideToggle({
  open,
  onClick,
}: {
  open: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`shrink-0 cursor-pointer rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors duration-200 ${
        open
          ? "border-border bg-muted/50 text-foreground"
          : "border-transparent bg-transparent text-muted-foreground hover:bg-muted/40 hover:text-foreground"
      }`}
      aria-expanded={open}
      aria-controls="affect-guide-drawer"
      title={open ? "收起模块说明" : "展开模块说明"}
    >
      <span className="inline-flex items-center gap-1.5">
        {open ? (
          <ChevronRight className="h-3.5 w-3.5" aria-hidden />
        ) : (
          <BookOpen className="h-3.5 w-3.5" aria-hidden />
        )}
        模块说明
      </span>
    </button>
  );
}
