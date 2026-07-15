import { Button } from "@/components/ui/button";

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
      <Button
        type="button"
        variant="link"
        className="eval-domain-breadcrumb__back h-auto p-0 text-inherit"
        onClick={onBack}
      >
        ‹ 总览
      </Button>
      <span className="eval-domain-breadcrumb__sep">/</span>
      <span className="eval-domain-breadcrumb__current">{domainLabel}</span>
      {meta ? <span className="eval-domain-breadcrumb__meta">{meta}</span> : null}
    </div>
  );
}
