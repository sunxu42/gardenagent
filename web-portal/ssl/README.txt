GardenAI 开发用 HTTPS（自签名证书）
================================

1. 编辑 openssl-san.cnf，把 IP.2 改成你电脑在局域网中的 IPv4（与浏览器地址栏里输入的 IP 一致）。

2. 在 PowerShell 中执行（可在本目录）：
   powershell -ExecutionPolicy Bypass -File .\generate-cert.ps1
   若未找到 openssl，可安装 Git for Windows，或使用已带 openssl 的 conda 环境。

3. 生成文件：gardenagent.crt、gardenagent.key（已加入 .gitignore，勿提交私钥到公开仓库）。

4. nginx 配置为 listen 8080 ssl 时，证书路径指向本目录。修改证书后重载 nginx：
   nginx.exe -s reload

5. Windows 防火墙放行 TCP 8080（入站规则）。

6. 浏览器访问：https://你的局域网IP:8080/
   首次会提示证书不受信任 →「高级」→「继续访问」即可；此后麦克风等 API 可在局域网使用。
   （当前 nginx 配置为 8080 仅 HTTPS，不再提供 http://IP:8080 明文访问。）
