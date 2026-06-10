import { BookOpen } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { smoothScrollContainer } from "../lib/affectGuideMotion";
import type { AffectLockState, AffectTurnRecord, EmotionProfile, RelationshipSnapshot, VadPoint } from "../types";
import { AffectBaselineDecayGuide } from "./affect/AffectBaselineDecayGuide";
import { AffectFlowDiagram } from "./affect/AffectFlowDiagram";
import { AffectGuideNav } from "./affect/AffectGuideNav";
import { AffectReferenceGuide } from "./affect/AffectReferenceGuide";
import { AffectStatusOverview } from "./affect/AffectStatusOverview";
import { GuideAnchorSection } from "./affect/GuideSection";

interface AffectGuidePanelProps {
  focusedRecord?: AffectTurnRecord | null;
  focusedRoundLabel?: string | null;
  currentRelationship?: RelationshipSnapshot | null;
  currentAgentVad?: VadPoint | null;
  emotionProfile?: EmotionProfile | null;
  agentBaselineVad?: VadPoint | null;
  affectLock: AffectLockState;
  onToggleAffectLock: (dimension: "relationship" | "agent_vad", refId: string) => void;
}

const GUIDE_SECTIONS = [
  { id: "affect-guide-s1", label: "关系与助手" },
  { id: "affect-guide-s2", label: "Baseline" },
  { id: "affect-guide-s3", label: "全链路" },
  { id: "affect-guide-s4", label: "V/A/D" },
] as const;

export function AffectGuidePanel({
  focusedRecord,
  focusedRoundLabel,
  currentRelationship,
  currentAgentVad,
  emotionProfile,
  agentBaselineVad,
  affectLock,
  onToggleAffectLock,
}: AffectGuidePanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState<string>(GUIDE_SECTIONS[0].id);
  const scrollLockRef = useRef(false);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (scrollLockRef.current) return;
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        const top = visible[0]?.target.id;
        if (top) setActiveId(top);
      },
      { root, rootMargin: "-18% 0px -52% 0px", threshold: [0, 0.2, 0.45] },
    );

    for (const { id } of GUIDE_SECTIONS) {
      const el = root.querySelector(`#${id}`);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  const scrollToSection = useCallback((id: string) => {
    const root = scrollRef.current;
    const el = root?.querySelector(`#${id}`);
    if (!root || !el) return;

    setActiveId(id);
    scrollLockRef.current = true;

    const rootRect = root.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    const targetTop = root.scrollTop + (elRect.top - rootRect.top);

    smoothScrollContainer(root, targetTop);

    window.setTimeout(() => {
      scrollLockRef.current = false;
    }, 520);
  }, []);

  return (
    <aside
      id="affect-guide-panel"
      className="affect-guide-drawer flex min-h-0 shrink-0 flex-col overflow-hidden"
      aria-label="情绪模块说明"
    >
      <header className="affect-rail-header shrink-0">
        <div className="affect-rail-header__row">
          <h3 className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
            <span className="affect-rail-header__icon">
              <BookOpen className="h-3.5 w-3.5" aria-hidden />
            </span>
            情绪模块说明
          </h3>
          <span className="invisible shrink-0 px-2.5 py-1.5 text-[11px]" aria-hidden>
            开发者
          </span>
        </div>
      </header>

      <AffectGuideNav
        items={GUIDE_SECTIONS}
        activeId={activeId}
        onSelect={scrollToSection}
      />

      <div
        ref={scrollRef}
        className="affect-panel-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-6 pt-2"
      >
        <div className="space-y-6">
          <GuideAnchorSection id="affect-guide-s1" title="关系与助手情绪" accent="amber">
            <AffectStatusOverview
              focusedRecord={focusedRecord}
              focusedRoundLabel={focusedRoundLabel}
              currentRelationship={currentRelationship}
              currentAgentVad={currentAgentVad}
              agentBaselineVad={agentBaselineVad}
              affectLock={affectLock}
              onToggleAffectLock={onToggleAffectLock}
            />
          </GuideAnchorSection>

          <GuideAnchorSection id="affect-guide-s2" title="Baseline" accent="slate">
            <AffectBaselineDecayGuide
              profile={emotionProfile}
              agentBaselineFallback={agentBaselineVad}
            />
          </GuideAnchorSection>

          <GuideAnchorSection id="affect-guide-s3" title="每轮全链路" accent="indigo">
            <AffectFlowDiagram />
          </GuideAnchorSection>

          <GuideAnchorSection id="affect-guide-s4" title="V/A/D 维度" accent="violet">
            <AffectReferenceGuide />
          </GuideAnchorSection>
        </div>
      </div>
    </aside>
  );
}
