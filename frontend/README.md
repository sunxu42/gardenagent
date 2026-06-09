# Frontend

移动优先 Web UI：聊天、`/config` 提示词编辑（`soul.yaml`）。

## 本地启动

```bash
npm install
npm run dev
```

开发服务器默认 `http://localhost:5173`，已将 `/ws` 代理到 `:8005`、`/api/prompt-editor` 代理到 `:8010`。

请先在项目根目录启动：

```bash
python src/server.py
python src/prompt-editor-server.py   # /config 与记忆导出需要
```

## 局域网 HTTPS 语音

本机 `localhost` 可直接使用麦克风。若通过手机或局域网 IP 访问，浏览器要求 HTTPS；证书生成见 `web-portal/ssl/README.txt`。
