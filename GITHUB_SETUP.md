# 🚀 Первая публикация на GitHub

Эта инструкция предназначена владельцу проекта. Команды выполняются из папки `Emoji & Sticker Info Bot`.

## 1. 🔐 Проверка секретных файлов

Убедитесь, что `.gitignore` исключает токен, окружение и локальную базу:

```powershell
git init
git check-ignore .env .venv data/bot.db
```

Команда должна вывести все три пути. Никогда не используйте `git add -f` для `.env` или `data/bot.db`.

## 2. 👤 Настройка автора коммитов

Настройки можно сохранить только для этого репозитория:

```powershell
git config user.name "YOUR_NAME"
git config user.email "YOUR_EMAIL"
```

Замените значения на имя и email, привязанный к GitHub.

## 3. 🌐 Создание репозитория

1. Откройте [github.com/new](https://github.com/new).
2. Укажите имя `emoji-sticker-info-bot`.
3. Выберите `Public` или `Private`.
4. Не добавляйте README, `.gitignore` и лицензию на стороне GitHub — они уже подготовлены локально.
5. Нажмите **Create repository**.

## 4. 📦 Первый коммит

Перед добавлением файлов обязательно просмотрите список:

```powershell
git status --short
git add .
git status
git commit -m "Initial release"
git branch -M main
```

В списке не должно быть `.env`, `.venv`, `data/bot.db`, `__pycache__` или `*.egg-info`.

## 5. ⬆️ Подключение GitHub и отправка

```powershell
git remote add origin https://github.com/YOUR_USERNAME/emoji-sticker-info-bot.git
git push -u origin main
```

Замените `YOUR_USERNAME` на имя аккаунта GitHub. Если remote уже существует:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/emoji-sticker-info-bot.git
```

## 6. 🔄 Следующие обновления

```powershell
git status
git add .
git commit -m "Describe the update"
git push
```

## 🛡️ Если токен случайно опубликован

Удаления файла из последующего коммита недостаточно: токен останется в истории Git. Сразу откройте BotFather, отзовите старый токен и выпустите новый. После этого обновите только локальный `.env`.

