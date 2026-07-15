# eval_fixtures — 评测场景与指标

结构化回归数据：按 **能力域 (domain) × 档位 (tier)** 组织，公共 API id 保持为 `{tier}/{stem}`。

## 目录

```
eval_fixtures/
├── taxonomy.yaml          # 能力域 + 受控 tags
├── snippets/              # 可复用 L0 断言块（assertion_sets）
├── metrics/               # LLM Judge 指标定义
└── scenarios/
    └── {domain}/
        ├── smoke/         # PR 冒烟（规则断言为主）
        └── judge/         # Nightly（+ LLM Judge）
```

当前 domain：`emotion` / `safety` / `persona` / `relationship` / `memory` / `tools` / `dialogue` / `transport`。

## 公共 id（稳定）

物理路径示例：`scenarios/emotion/smoke/emotion_anxious_01.yaml`  
对外 id：`smoke/emotion_anxious_01`

列表与运行接口均使用稳定 id。A2UI 重命名后旧 id（如 `smoke/a2ui_binary`）仍可通过别名解析。

## 命名约定

| 类型 | 建议 stem 形态 | 例子 |
|------|----------------|------|
| 情绪 | `emotion_{mood}_{variant}_nn` | `emotion_anxious_01` |
| 安全 | `boundary_{risk}_nn` | `boundary_crisis_01` |
| A2UI 用户触发 | `a2ui_user_{widget}_{variant}` | `a2ui_user_binary` |
| A2UI Agent 主动 | `a2ui_agent_init_{variant}` | `a2ui_agent_init_binary` |
| A2UI 负例 | `a2ui_negative_{case}` | `a2ui_negative_plain_qa` |
| 其它工具 | `tool_{name}_nn` | `tool_required_01` |

## smoke ↔ judge 配对

同 stem 的 judge 场景可用 `extends: smoke/{stem}` 继承 domain 与首轮话术：

```yaml
id: emotion_anxious_01
extends: smoke/emotion_anxious_01
tier: judge
tags: [mood_anxious, multi_turn]
setup:
  rounds: 3
user_driver:
  type: scripted
  turns_append:
    - text: "你觉得我是不是太矫情了？"
    - text: "我该怎么办？"
assertions: [...]
judge: { enabled: true, metrics: [...] }
```

子场景若声明 `assertions` / `assertion_sets`，**不会**继承 smoke 的完整 L0 契约。

## 覆盖矩阵（目标）

| Domain | smoke | judge | 备注 |
|--------|-------|-------|------|
| emotion | 每 mood ≥1 | 代表性多轮 | L0 用 `emotion_smoke_base` snippet |
| safety | crisis / medical / jailbreak / identity | crisis + medical | |
| tools | A2UI 用户/主动/负例 + MCP | **smoke_only** | `judge_expected: false` |
| memory | recall + cross_session | **smoke_only** | |
| persona | greeting / name | warmth / comfort | |
| relationship | thanks | thanks + trust | |
| dialogue | followup / context | followup | |
| transport | latency | **smoke_only** | |

## 场景 YAML

必填：`id`、`domain`、`tags`、`tier`、`user_driver`。

可选：

```yaml
assertion_sets:
  - emotion_smoke_base   # 先展开 snippets/*.yaml
assertions:
  - type: assistant_max_length
    name: concise_reply
    max_chars: 120
```

常用断言类型：`assistant_not_contains` / `assistant_contains` / `assistant_min_length` / `assistant_max_length` / `tool_called` / **`tool_not_called`** / `text_not_matches` / `agent_emotion_in`。

## Emotion smoke 契约

`assertion_sets: [emotion_smoke_base]` 提供 3 条共用禁词断言；场景本地再补：

1. `assistant_max_length`（通常 120，happy/surprised 为 140）
2. 语气禁词（`no_harsh_tone` / `no_dismissal` 等）
3. `assistant_contains`（呼应用户关键词）
4. `assistant_min_length`

合起来仍是 README/eval 约定的约 7 条 L0 检查。
