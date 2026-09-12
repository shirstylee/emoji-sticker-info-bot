$ErrorActionPreference = "Stop"

$EmojiBotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $EmojiBotRoot

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    throw "Не найдено локальное окружение .venv. Сначала запустите .\setup.ps1"
}

if (-not (Test-Path -LiteralPath ".env")) {
    throw "Не найден .env. Скопируйте .env.example в .env и добавьте BOT_TOKEN."
}

& ".venv\Scripts\python.exe" -m emoji_id_bot.main
exit $LASTEXITCODE
