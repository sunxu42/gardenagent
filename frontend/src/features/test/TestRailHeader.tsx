import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface TestRailHeaderProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function TestRailHeader({
  icon: Icon,
  title,
  subtitle,
  actions,
}: TestRailHeaderProps): JSX.Element {
  return (
    <header className="affect-rail-header shrink-0">
      <div className="affect-rail-header__row">
        <div className="min-w-0 flex-1">
          <h3 className="flex min-w-0 items-center gap-2 text-sm font-medium text-muted-foreground">
            <span className="affect-rail-header__icon">
              <Icon className="h-3.5 w-3.5" aria-hidden />
            </span>
            <span className="truncate">{title}</span>
          </h3>
          {subtitle ? (
            <p className="mt-0.5 truncate pl-[calc(1.5rem+0.5rem)] text-[11px] leading-snug text-muted-foreground">
              {subtitle}
            </p>
          ) : null}
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </header>
  );
}
