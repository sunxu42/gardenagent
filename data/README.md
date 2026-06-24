# data — 可版本管理的数据

`data/` 存放应纳入 Git 的提示词、评测 fixture 和 Agent 配置。运行时产生的可变产物（对话 checkpoint、评测结果、FAISS 索引等）放在 `runtime/`（已 gitignore）。

## 目录结构

```
data/
├── prompts/                  # 智能体提示词与情感策略
│   ├── soul.yaml             # 灵魂文件（人设 + few-shot）
│   ├── agent_mood.yaml       # Agent 心情模板
│   ├── affective.yaml        # 用户侧回应策略
│   └── manifest.yaml         # Prompt Composer 清单（可选）
├── eval_fixtures/
│   ├── scenarios/
│   │   ├── smoke/            # 冒烟回归场景
│   │   └── judge/              # 需 LLM Judge 的场景
│   └── metrics/                # Judge 指标定义
├── agent_configs/
│   ├── mcp_servers.yaml      # MCP 端点（供 agent/manager.py）
│   └── subagents.yaml        # 子 Agent 配置
└── reference/                # 种子文档与技能参考
    ├── SOUL.md
    ├── AGENTS.md
    └── skills/
```

## 各目录用途

| 目录 | 消费者 | 说明 |
|------|--------|------|
| `prompts/` | `agent/middlewares/`、`server/api/prompt_editor/` | 每轮热加载；可通过前端 `/config` 编辑 `soul.yaml` |
| `eval_fixtures/` | `eval/domain/` | 场景 YAML 与 Judge 指标；路径由 `shared/config/paths.py` 解析 |
| `agent_configs/` | `agent/manager.py` | MCP 连接、子 Agent 声明 |
| `reference/` | 开发参考 | 不参与运行时自动加载 |

## 提示词编辑

启动 `python -m server` 后：

- **Web UI**：聊天页笔形图标 → `/config`（桌面三栏，仅 `soul.yaml` 支持表单编辑）
- **HTTP API**：`/api/prompt-editor/`（详见 `server/api/prompt_editor/`）

`PersonaPromptMiddleware` 按通用模板渲染 `soul.yaml` 为 system prompt，修改后下一轮对话即生效，无需重启。

## 记忆导出（可选）

启用 Mem0 后，可通过 `/api/prompt-editor/memory-yaml/refresh` 导出只读 `data/prompts/memory/memory.yaml`（gitignore，不参与对话注入）。

## 从旧结构迁移

若仍保留 `base/` 与 `roles/Lora.yaml` 备份，可运行：

```bash
python scripts/merge_soul_yaml.py
```

将旧结构合并为当前 `soul.yaml`。
