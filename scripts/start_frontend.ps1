$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"

Set-Location $FrontendDir
Write-Host "Serving frontend at http://127.0.0.1:8080"
Write-Host "Make sure the backend is running on http://127.0.0.1:8000"
python -m http.server 8080 --bind 127.0.0.1
