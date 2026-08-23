$ErrorActionPreference = "Stop"

$EmojiBotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $EmojiBotRoot

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Создан .env — вставьте в него токен от @BotFather."
}

Write-Host "Готово. Все зависимости находятся только в .venv."

