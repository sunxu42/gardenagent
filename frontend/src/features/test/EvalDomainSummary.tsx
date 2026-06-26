import type { DomainRadarPoint } from "@/features/test/coverageRadarModel";

interface EvalDomainSummaryProps {
  point: DomainRadarPoint | null;
  onEnter: () => void;
}

function collectMissingTags(point: DomainRadarPoint): string[] {
  const tags = new Set<string>();
  for (const cell of [point.smoke, point.judge]) {
    for (const tag of cell?.tags_missing ?? []) {
      tags.add(tag);
    }
  }
  return [...tags];
}

export function EvalDomainSummary({ point, onEnter }: EvalDomainSummaryProps): JSX.Element {
  if (!point) {
    return (
      <div className="eval-domain-summary eval-domain-summary--empty">
        <p className="text-[11px] text-muted-foreground">选择能力域查看覆盖摘要，或点击下方域按钮进入测试</p>
      </div>
    );
  }

  const missingTags = collectMissingTags(point);
  const scenarioCount =
    (point.smoke?.scenario_count ?? 0) + (point.judge?.scenario_count ?? 0);

  return (
    <div className="eval-domain-summary">
      <h3 className="eval-domain-summary__title">{point.domain_label}</h3>
      <p className="eval-domain-summary__metrics">
        场景覆盖 {Math.round(point.coverage_score * 100)}% · 通过率{" "}
        {Math.round(point.pass_score * 100)}% · {scenarioCount} 个场景
      </p>

      {missingTags.length > 0 ? (
        <div className="eval-domain-summary__tags">
          {missingTags.map((tag) => (
            <span key={tag} className="eval-coverage-tag eval-coverage-tag--missing">
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      <button className="eval-domain-summary__enter" type="button" onClick={onEnter}>
        进入测试
      </button>
    </div>
  );
}
