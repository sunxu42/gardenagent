import type { A2UIMessage } from "a2ui-shadcn";

const A2UI_VERSION = "v0.9" as const;
const DEFAULT_CATALOG_ID = "shadcn";

interface PlanInput {
  id: string;
  label: string;
  description?: string;
}

export function renderPlanSelector(params: {
  title: string;
  plans: PlanInput[];
  surface_id?: string;
}): A2UIMessage[] {
  const surfaceId = params.surface_id ?? "single-select-cards";
  const planChildren: string[] = [];
  const components: Record<string, unknown>[] = [
    { id: "root", component: "Card", children: ["title", "plan-list"] },
    { id: "title", component: "Text", text: params.title, variant: "h3" },
    { id: "plan-list", component: "Column", children: planChildren },
  ];

  params.plans.forEach((plan, index) => {
    const planId = (plan.id || `plan-${index + 1}`).trim();
    const label = (plan.label || planId).trim();
    const cardId = `plan-${planId}`;
    planChildren.push(cardId);
    const card: Record<string, unknown> = {
      id: cardId,
      component: "PlanOptionCard",
      planId,
      title: label,
      action: {
        event: {
          name: "confirm_plan",
          context: { planId },
        },
      },
    };
    if (plan.description?.trim()) {
      card.description = plan.description.trim();
    }
    components.push(card);
  });

  return [
    { version: A2UI_VERSION, createSurface: { surfaceId, catalogId: DEFAULT_CATALOG_ID } },
    { version: A2UI_VERSION, updateComponents: { surfaceId, components } },
    { version: A2UI_VERSION, updateDataModel: { surfaceId, path: "/selectedPlan", value: null } },
  ] as A2UIMessage[];
}
