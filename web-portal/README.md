# GardenAI Web 门户（web-portal）

浏览器端控制台：连接多模态服务（WebSocket）、文本/语音会话、编辑 `yard/prompts` 下 YAML（依赖本机 `prompt-editor-server`）。

本机可直接打开 **`index.html`**；若希望 **局域网内其他设备** 通过 **`https://你的IP:8080`** 访问（含麦克风等需 **HTTPS 安全上下文** 的能力），请按下文配置 **nginx + TLS**。

---

## 一、本机先启动的后端

在仓库根目录 `gardenagent` 下执行（两个进程都要开）：

```bash
python src/server.py
python src/prompt-editor-server.py
```

| 服务 | 默认监听 | 用途 |
|------|-----------|------|
| `server.py` | `0.0.0.0:8005` | WebSocket，nginx 将 `/ws` 反代到此端口 |
| `prompt-editor-server.py` | `0.0.0.0:8010` | `yard/prompts` YAML 编辑 API；nginx 将 **`/api/prompt-editor/`** 反代到此端口 |

8005 / 8010 **不必对局域网单独放行**，只要本机 nginx 能访问 `127.0.0.1` 即可。

---

## 二、TLS 证书（自签名，局域网开发用）

麦克风等 API 要求 **安全上下文**：用局域网 IP 访问时必须是 **HTTPS**，因此需要证书。

1. 编辑 **`ssl/openssl-san.cnf`**：把 **`IP.2`** 改成 **`ipconfig` 里本机 IPv4**（与浏览器地址栏里输入的 IP 一致）。
2. 在 **`ssl`** 目录生成证书（需 OpenSSL，可用 [Git for Windows](https://git-scm.com/download/win) 自带的 `C:\Program Files\Git\usr\bin\openssl.exe`）：

```powershell
cd D:\Codes\gardenagent\web-portal\ssl
powershell -ExecutionPolicy Bypass -File .\generate-cert.ps1
```

生成 **`gardenagent.crt`**、**`gardenagent.key`**（见 **`ssl/.gitignore`**，勿把私钥提交到公开仓库）。

也可手动执行（路径按你本机 OpenSSL 调整）：

```powershell
& "C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -nodes -days 730 -newkey rsa:2048 `
  -keyout gardenagent.key -out gardenagent.crt `
  -config openssl-san.cnf -extensions v3_req
```

更多说明见 **`ssl/README.txt`**。

---

## 三、nginx 配置

目标：**仅 HTTPS、对外端口 8080**（与当前仓库配套示例一致）。

1. 在 **`http { }`** 内增加或合并一个 `server`，要点如下（路径请按你机器修改）：
   - **`listen 8080 ssl;`**
   - **`root`** 指向本目录 **`web-portal`** 的绝对路径（Windows 可用 `D:/Codes/gardenagent/web-portal`）
   - **`ssl_certificate`** / **`ssl_certificate_key`** 指向上一步的 **`.crt`** / **`.key`**
   - **`location /ws`** → **`proxy_pass http://127.0.0.1:8005;`**，并设置 WebSocket 升级头
   - **`location /api/prompt-editor/`** → **`proxy_pass http://127.0.0.1:8010/api/prompt-editor/;`**（路径前缀需与后端一致）

可参考仓库内 **`nginx-lan-proxy.server.conf.example`**，整段复制进你的 `nginx.conf` 的 `http` 块后，再改 **`root`** 与证书路径。

2. 检查并重载：

```bash
nginx -t
nginx -s reload
```

（Windows 下在 nginx 安装目录执行，或使用完整路径。）

**说明：** 同一端口不能同时提供明文 HTTP 与 HTTPS；当前方案下 **`http://IP:8080` 不可用**，请统一使用 **`https://IP:8080`**。

---

## 四、Windows 防火墙

新建 **入站规则**，允许 **TCP 8080**（对外只开这一端口即可）。

---

## 五、浏览器访问与前端行为

- 访问：**`https://你的局域网IPv4:8080/`**
- 自签名证书会提示不安全 → **高级** → **继续访问**（正常现象）。
- 页面脚本在「非 localhost 的 HTTPS」下会自动使用 **`wss://当前主机:8080/ws`**，并把提示词 API 基址设为 **`location.origin`**（与同源 **`/api/prompt-editor/`** 一致）。
- 若仅在本机调试、不需要麦克风，也可用 **`http://127.0.0.1:8080`** —— 前提是 nginx 仍对该端口提供 **HTTP**；若你按上文只配置了 **`listen 8080 ssl`**，则本机也必须使用 **`https://127.0.0.1:8080`**。

---

## 六、目录与文件速查

| 路径 | 说明 |
|------|------|
| `index.html` / `index.js` / `index.css` | 主门户 |
| `libopus.js` | 语音解码依赖，与 `index.html` 同目录部署 |
| `ssl/` | 证书配置与生成脚本 |
| `nginx-lan-proxy.server.conf.example` | nginx `server` 示例片段 |

---

## 七、常见问题

- **麦克风报错、`mediaDevices` 不可用：** 多为用 **`http://局域网IP`** 打开。请改用 **`https://`**，或仅在本机使用 **`http://localhost`** / **`127.0.0.1`**（且 nginx 若仅 ssl 则仍用 https）。
- **证书与访问 IP 不一致：** 重新编辑 **`openssl-san.cnf` 的 IP.2**，再运行 **`generate-cert.ps1`**，然后 **`nginx -s reload`**。
- **`generate-cert.ps1` 中文乱码报错：** 脚本已改为英文输出；请拉取最新文件或使用 **`ssl/README.txt`** 中的手动 openssl 命令。
