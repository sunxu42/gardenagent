# prompt_editor — 提示词编辑 HTTP API

`prompt_editor/` 提供 `data/prompts/` 的 HTTP 读写与记忆管理接口，供前端 `/config` 与记忆面板使用。

## 职责

| 能力 | 实现位置 |
|------|----------|
| HTTP 路由 | `api/routes.py` |
| 路径安全与目录树 | `api/core.py` |

## 主要 API

| 路径 | 说明 |
|------|------|
| `GET /api/prompt-editor/prompts-yaml/tree` | 列出 prompts 目录树 |
| `GET /api/prompt-editor/prompts-yaml/content` | 读取 YAML |
| `PUT /api/prompt-editor/prompts-yaml/content` | 保存 YAML |
| `POST /api/prompt-editor/user-data/clear` | 清除用户记忆数据 |
| `POST /api/prompt-editor/memory-yaml/refresh` | 从 Mem0 导出 `memory.yaml` |

## 与外部模块的关系

- **挂载点**：`server/app.py` 调用 `create_prompt_editor_routes(prompts_root)`
- **数据**：读写 `data/prompts/`（路径由 `shared.config.paths.resolve_prompts_dir()` 解析）
- **Agent**：清用户数据、Mem0 导出（懒 import `agent.memory`）
- **前端**：`frontend/src/features/config/`、`frontend/src/services/promptEditorApi.ts`

API 随 `python -m server` 一同启动，无需单独进程。
