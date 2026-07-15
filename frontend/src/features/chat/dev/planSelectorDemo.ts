import type { A2UIMessage } from "a2ui-shadcn";

export const PLAN_SELECTOR_DEMO_SURFACE_ID = "plan-selector-demo";

export const planSelectorDemoMessages: A2UIMessage[] = [
  {
    version: "v0.9",
    createSurface: {
      surfaceId: PLAN_SELECTOR_DEMO_SURFACE_ID,
      catalogId: "shadcn",
    },
  },
  {
    version: "v0.9",
    updateComponents: {
      surfaceId: PLAN_SELECTOR_DEMO_SURFACE_ID,
      components: [
        { id: "root", component: "Card", children: ["title", "plan-list"] },
        { id: "title", component: "Text", text: "A2UI 方案选择（自定义卡片）", variant: "h3" },
        { id: "plan-list", component: "Column", children: ["plan-plan-a", "plan-plan-b"] },
        {
          id: "plan-plan-a",
          component: "PlanOptionCard",
          planId: "plan-a",
          title: "方案 A · 轻量迭代",
          description: "在现有架构上小步优化，风险低、上线快。",
          action: {
            event: {
              name: "confirm_plan",
              context: { planId: "plan-a" },
            },
          },
        },
        {
          id: "plan-plan-b",
          component: "PlanOptionCard",
          planId: "plan-b",
          title: "方案 B · 完整重构",
          description: "重新设计核心模块，长期维护成本更低。",
          action: {
            event: {
              name: "confirm_plan",
              context: { planId: "plan-b" },
            },
          },
        },
      ],
    },
  },
  {
    version: "v0.9",
    updateDataModel: {
      surfaceId: PLAN_SELECTOR_DEMO_SURFACE_ID,
      path: "/selectedPlan",
      value: null,
    },
  },
];
