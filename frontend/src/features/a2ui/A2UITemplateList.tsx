import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { A2UITemplateCatalogEntry } from "./types";

interface A2UITemplateListProps {
  templates: A2UITemplateCatalogEntry[];
  selectedId: string;
  onSelect: (templateId: string) => void;
}

export function A2UITemplateList({ templates, selectedId, onSelect }: A2UITemplateListProps) {
  return (
    <aside className="flex min-h-0 w-[220px] shrink-0 flex-col bg-[var(--apple-grouped-bg)]">
      <div className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--apple-secondary-label)]">
        模板列表
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {templates.map((template) => {
          const selected = template.id === selectedId;
          return (
            <li key={template.id}>
              <Button
                type="button"
                variant="ghost"
                onClick={() => onSelect(template.id)}
                className={cn(
                  "mb-1 h-auto w-full justify-start rounded-[var(--apple-radius-md)] px-3 py-2.5 text-left font-normal shadow-none",
                  selected
                    ? "bg-[var(--apple-cell-bg)] text-[var(--apple-label)] hover:bg-[var(--apple-cell-bg)]"
                    : "bg-transparent text-[var(--apple-label)] hover:bg-[var(--apple-cell-bg)]/70",
                )}
              >
                <div className="w-full text-left">
                  <div className="text-sm font-medium">{template.name}</div>
                  <div className="mt-1 line-clamp-2 text-xs leading-relaxed text-[var(--apple-secondary-label)]">
                    {template.scenario}
                  </div>
                  <div className="mt-1.5 font-mono text-[10px] text-[var(--apple-secondary-label)]">
                    {template.tool_name}
                  </div>
                </div>
              </Button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
