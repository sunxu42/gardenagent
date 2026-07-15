import { BookOpen } from "lucide-react";
import type { SourceItem } from "../../lib/affectSources";

interface AffectSourceListProps {
  title?: string;
  items: SourceItem[];
}

export function AffectSourceList({ title = "判断来源", items }: AffectSourceListProps) {
  if (items.length === 0) return null;

  return (
    <div className="affect-guide-inset affect-guide-inset--sky p-2.5">
      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-foreground">
        <BookOpen className="h-3.5 w-3.5 text-primary" aria-hidden />
        {title}
      </p>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={`${item.label}-${item.detail.slice(0, 24)}`} className="text-xs leading-relaxed">
            <span className="font-medium text-foreground/90">{item.label}</span>
            <span className="text-muted-foreground"> — </span>
            <span className="text-foreground/80">{item.detail}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
