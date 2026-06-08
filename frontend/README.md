# Frontend Chat

`frontend` 是独立部署的移动优先聊天前端，仅提供对话能力。

## 职责边界

- 提供消息输入、消息流式展示与连接状态提示。
- 不提供参数编辑、日志、控制类入口。
- 参数编辑继续通过 `web-portal` 完成，由服务端在会话建立时读取生效。

## 本地启动

```bash
npm install
npm run dev
```

默认通过 `ws://<当前主机>:8005` 连接后端，请先在项目根目录启动：

```bash
python src/server.py
```
