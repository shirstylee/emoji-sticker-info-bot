# 🚀 Открытие репозитория на GitHub

Проект уже связан с [shirstylee/emoji-sticker-info-bot](https://github.com/shirstylee/emoji-sticker-info-bot), основная ветка — `main`. Повторно создавать репозиторий или выполнять `git init` не требуется.

## 1. 🔎 Проверка локальных файлов и истории

Выполните из папки `emoji-sticker-info-bot`:

```powershell
.\setup.ps1
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_publication.py --history
.\.venv\Scripts\python.exe -m pip_audit --local --skip-editable
git check-ignore .env .venv data/bot.db
git status --short
```

Проверка публикации читает рабочие файлы, Git-индекс и все локальные ветки/теги, включая старые версии удалённых файлов. Она ищет известные форматы токенов, приватных ключей и служебные файлы; значения секретов не выводятся. Наличие `.env` в `.gitignore` само по себе не защищает старые коммиты.

Эта проверка не просматривает данные на GitHub, которых нет локально. Если есть другие удалённые ветки, сначала обновите локальные ссылки через `git fetch origin --prune --tags` и повторите её. Отдельно просмотрите вложения Issues, Actions-логи и артефакты, если они существуют.

Имя и email авторов коммитов также станут публичными. Проверьте их локально:

```powershell
git log --all --format="%h %an <%ae>"
```

Для будущих коммитов можно указать GitHub noreply-адрес из [настроек email](https://github.com/settings/emails) через `git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"`. Это не меняет старую историю.

## 2. 📜 Лицензия

В проект добавлены `LICENSE` (GNU AGPLv3), `NOTICE` и информация об авторстве. Лицензия позволяет форки и коммерческое использование, но требует сохранять уведомления об авторстве и соблюдать условия раскрытия исходников при распространении и сетевом использовании изменённых версий. Подробности — в [README](README.md#-лицензия-и-авторство).

## 3. 📦 Сохранение подготовленных изменений

```powershell
git diff --check
git diff
git add .
git diff --cached --stat
.\.venv\Scripts\python.exe scripts/check_publication.py --history
git commit -m "chore: prepare repository for public release"
git push origin main
```

Перед коммитом просмотрите список добавленных файлов. Никогда не добавляйте `.env`, `.venv` и пользовательские данные с `git add -f`.

## 4. ✅ Проверки GitHub

После push откройте [Actions](https://github.com/shirstylee/emoji-sticker-info-bot/actions) и дождитесь успешного workflow **CI**. Для тестов не нужен `BOT_TOKEN`; не добавляйте рабочий токен бота в GitHub Actions.

В **Settings → Advanced Security** включите доступные для репозитория Dependabot alerts, secret scanning, push protection и **Private vulnerability reporting**. Конфигурация Dependabot уже в проекте; эти переключатели на GitHub включаются отдельно. Некоторые возможности могут стать доступны после перехода в Public.

## 5. 🌐 Открытие репозитория

На странице репозитория откройте **Settings → General → Danger Zone → Change repository visibility**, выберите **Public** и подтвердите изменение. Это отдельное действие на GitHub — локальные файлы не меняют видимость репозитория.

Перед подтверждением GitHub показывает последствия. Публичными становятся в том числе история коммитов и Actions-логи. [Официальная инструкция GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).

После открытия проверьте отображение баннера, README и лицензии, работу формы приватного сообщения об уязвимости и доступные настройки защиты.

## 🛡️ Если найден токен

Сначала отзовите его через BotFather и замените только в локальном `.env`. Удаление из последнего коммита не убирает значение из истории. Не открывайте репозиторий с действующим токеном; очистку истории согласуйте отдельно, поскольку она меняет коммиты.

Документация: [настройка приватных сообщений об уязвимостях](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
