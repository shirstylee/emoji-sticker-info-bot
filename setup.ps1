$ErrorActionPreference = "Stop"

$EmojiBotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $EmojiBotRoot

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось создать .venv. Проверьте установку Python 3.11 или новее."
    }
}

& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    throw "Не удалось установить зависимости в .venv. Исправьте ошибку и повторите запуск."
}

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Создан .env — вставьте в него токен от @BotFather."
}

Write-Host "Готово. Все зависимости находятся только в .venv."
