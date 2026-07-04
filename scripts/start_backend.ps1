$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\pip install -r backend\requirements.txt"
}

Set-Location (Join-Path $Root "backend")
Write-Host "Starting backend at http://127.0.0.1:8000"
Write-Host "API docs: http://127.0.0.1:8000/docs"
& $VenvPython app.main:app --reload --host 127.0.0.1 --port 8000
