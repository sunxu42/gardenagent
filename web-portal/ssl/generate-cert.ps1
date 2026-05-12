# Run from this folder:
#   powershell -ExecutionPolicy Bypass -File .\generate-cert.ps1
# Requires OpenSSL (e.g. Git for Windows: C:\Program Files\Git\usr\bin\openssl.exe)
# Edit openssl-san.cnf IP.2 to your LAN IPv4 before running.

$ErrorActionPreference = "Stop"
$sslDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$openssl = $null
foreach ($c in @(
    "openssl",
    "C:\Program Files\Git\usr\bin\openssl.exe",
    "C:\Program Files (x86)\Git\usr\bin\openssl.exe"
)) {
    if ($c -eq "openssl") {
        $g = Get-Command openssl -ErrorAction SilentlyContinue
        if ($g) { $openssl = $g.Source; break }
    } elseif (Test-Path $c) { $openssl = $c; break }
}
if (-not $openssl) {
    Write-Error "openssl not found. Install Git for Windows or add openssl to PATH."
}

$key  = Join-Path $sslDir "gardenagent.key"
$cert = Join-Path $sslDir "gardenagent.crt"
$cnf  = Join-Path $sslDir "openssl-san.cnf"

if (-not (Test-Path $cnf)) {
    Write-Error "Missing openssl-san.cnf"
}

Write-Host "Config: $cnf"
Write-Host "Writing: $key and $cert (730 days)"
& $openssl req -x509 -nodes -days 730 -newkey rsa:2048 `
    -keyout $key -out $cert -config $cnf -extensions v3_req

Write-Host "Done. Point nginx ssl_certificate / ssl_certificate_key to these files."
Write-Host "If IP.2 in openssl-san.cnf is wrong, fix it and run this script again."
Write-Host "Then: nginx.exe -s reload"
