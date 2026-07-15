"""Render A2UI system prompt and tool descriptions from catalog."""

from __future__ import annotations

from typing import Any

from agent.a2ui.catalog import get_template, list_templates

_TOOL_ORDER: list[tuple[str, str]] = [
    (
        "single_select",
        "恰好选一项 → show_single_select，并设置 variant："
        "binary（2 个短互斥动作）/ emoji（带表情）/ cards（带说明的方案）/ default（其它）",
    ),
    ("multi_select", "需勾选一项或多项 → show_multi_select"),
    ("date_picker", "需选择具体年月日（生日/出行/纪念日）→ show_date_picker"),
    (
        "data_table",
        "≥3 条结构化记录（对比/时间线/按年列举）→ show_data_table；"
        "只读列举用 interactive=false，需点选一行用 interactive=true",
    ),
]

_STRUCTURED_LIST_RULES = [
    (
        "当用户要求 **列举/整理/汇总** 多条结构化事实（如「近10年台风」「历年大事」），"
        "或你准备给出 **≥3 行、每行含至少 2 个维度**（年份+名称+说明等）→ "
        "必须调用 show_data_table(interactive=false)。"
    ),
    "禁止在正文用「2015年…2016年…」或 bullet 列表逐条写完；表格放 tool，正文最多一句补充。",
    "短口语举例（1-2 个词、无表格结构，如「猫狗鸟都是哺乳动物」）仍可用口语，不必调 table。",
]

_POST_CALL_RULES = [
    (
        "show_single_select / show_multi_select / "
        "show_date_picker / show_data_table(interactive=true) 成功后："
        "正文最多一句口语邀请点选，禁止重复选项列表。"
    ),
    (
        "show_data_table(interactive=false) 成功后："
        "正文最多一句口语，禁止重复表格全文。"
    ),
]

_NEGATIVE_EXAMPLES = [
    "错误：正文「第一去海边，第二去博物馆，你选哪个？」",
    "错误：正文「回复 1、2、3 告诉我」",
    "错误：用户要「列举近10年台风」，正文逐条写 2015年彩虹、2016年莫兰蒂…",
    "正确：先 show_data_table(interactive=false) 展示年份/台风/影响，正文「表里列好了，想聊哪年跟我说！」",
    "正确：先调用 show_single_select(variant=cards)，正文「点卡片选一个吧！」",
]


def _lines_for_template(entry: dict[str, Any]) -> list[str]:
    tool_name = str(entry.get("tool_name") or "")
    scenario = str(entry.get("scenario") or "").strip()
    triggers = [str(x).strip() for x in entry.get("trigger_examples") or [] if str(x).strip()]
    agent_triggers = [
        str(x).strip() for x in entry.get("agent_initiated_triggers") or [] if str(x).strip()
    ]
    anti = [str(x).strip() for x in entry.get("anti_patterns") or [] if str(x).strip()]
    lines = [f"- **{tool_name}**（{entry.get('name', '')}）：{scenario}"]
    if triggers:
        lines.append(f"  用户请求示例：{'；'.join(triggers[:3])}")
    if agent_triggers:
        lines.append(f"  Agent 主动示例：{'；'.join(agent_triggers[:3])}")
    if anti:
        lines.append(f"  禁止：{'；'.join(anti[:2])}")
    return lines


def _collect_selection_signals() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for entry in list_templates():
        for raw in entry.get("selection_intent_signals") or []:
            text = str(raw).strip()
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out


def _collect_structured_list_signals() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for entry in list_templates():
        for raw in entry.get("structured_list_signals") or []:
            text = str(raw).strip()
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out


def render_a2ui_system_prompt() -> str:
    """Build stable A2UI rules block for system prompt injection."""
    templates = {item["id"]: item for item in list_templates()}
    tool_lines: list[str] = []
    for template_id, hint in _TOOL_ORDER:
        entry = templates.get(template_id)
        if entry:
            tool_lines.append(hint)
            tool_lines.extend(_lines_for_template(entry))

    signals = _collect_selection_signals()
    signal_text = "、".join(f"「{signal}」" for signal in signals[:12])
    list_signals = _collect_structured_list_signals()
    list_signal_text = "、".join(f"「{signal}」" for signal in list_signals[:12])

    sections = [
        "## A2UI 交互规则",
        "",
        "### 何时必须使用 UI（含 Agent 主动抛选项）",
        (
            "- 当你打算提供 **≥2 个可选项** 且 **等待用户选择**"
            "（无论用户是否先要求列举）→ 必须先调用 show_* A2UI tool。"
        ),
        (
            "- Agent 主动场景：打算说「我们可以玩 A、B、C」「你想选哪个难度」"
            "「接下来有两条路」→ 先调 tool，禁止正文用 1/2/3 或「第一/第二」列完。"
        ),
        "- 纯讲解、无结构化表、无待选选项 → 口语即可，不调 A2UI tool。",
        "- 短口语举例（1-2 个词、无表格结构）→ 可用口语，不调 UI tool。",
        f"- 选择意图信号：{signal_text}",
        "",
        "### 决策顺序",
        "- 需要具体年月日 → show_date_picker",
        "- ≥3 行且 ≥2 维的结构化列举/对比 → show_data_table",
        "- 可勾多项 → show_multi_select",
        "- 恰好选一个 → show_single_select，再选 variant（binary / emoji / cards / default）",
        "- 其它讲解 → 不调 A2UI",
        "",
        "### 结构化列举 → show_data_table",
        *[f"- {rule}" for rule in _STRUCTURED_LIST_RULES],
        f"- 结构化列举信号：{list_signal_text}",
        "",
        "### 工具选择",
        *tool_lines,
        "",
        "### 调用后正文约束",
        *[f"- {rule}" for rule in _POST_CALL_RULES],
        "",
        "### 反例（禁止）",
        *[f"- {item}" for item in _NEGATIVE_EXAMPLES],
    ]
    return "\n".join(sections).strip()


def build_tool_description(template_id: str) -> str:
    """Build LangChain tool description from one catalog entry."""
    entry = get_template(template_id)
    scenario = str(entry.get("scenario") or "").strip()
    triggers = [str(x).strip() for x in entry.get("trigger_examples") or [] if str(x).strip()]
    agent_triggers = [
        str(x).strip() for x in entry.get("agent_initiated_triggers") or [] if str(x).strip()
    ]
    anti = [str(x).strip() for x in entry.get("anti_patterns") or [] if str(x).strip()]

    parts = [
        f"向用户展示 {entry.get('name', 'A2UI')} 卡片（A2UI）。",
        scenario,
    ]
    if triggers:
        parts.append(f"用户请求场景：{'；'.join(triggers[:2])}。")
    if agent_triggers:
        parts.append(f"Agent 主动场景：{'；'.join(agent_triggers[:2])}。")
    if anti:
        parts.append(f"禁止：{'；'.join(anti[:2])}。")
    parts.append("调用后正文最多一句简短邀请，不要重复选项全文或粘贴 JSON。")
    return "".join(parts)
