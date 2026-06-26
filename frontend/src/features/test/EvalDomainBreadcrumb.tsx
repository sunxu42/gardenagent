interface EvalDomainBreadcrumbProps {
  domainLabel: string;
  onBack: () => void;
  meta?: string;
}

export function EvalDomainBreadcrumb({
  domainLabel,
  onBack,
  meta,
}: EvalDomainBreadcrumbProps): JSX.Element {
  return (
    <div className="eval-domain-breadcrumb">
      <button className="eval-domain-breadcrumb__back" type="button" onClick={onBack}>
        ‹ 总览
      </button>
      <span className="eval-domain-breadcrumb__sep">/</span>
      <span className="eval-domain-breadcrumb__current">{domainLabel}</span>
      {meta ? <span className="eval-domain-breadcrumb__meta">{meta}</span> : null}
    </div>
  );
}
