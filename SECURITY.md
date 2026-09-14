# 🔒 Сообщение об уязвимости / Security policy

Исправления безопасности выпускаются для актуального кода в ветке `main`.

## Приватное сообщение / Private report

Используйте [Report a vulnerability](https://github.com/shirstylee/emoji-sticker-info-bot/security/advisories/new), если владелец включил private vulnerability reporting.

Если форма недоступна, создайте Issue только с просьбой предоставить приватный канал связи. Не публикуйте детали эксплуатации, токены или данные пользователей.

Include the affected commit, reproduction steps, impact and a minimal example with synthetic data in the private report. If private reporting is unavailable, open an issue asking for a private contact channel without disclosing the vulnerability.

Не проводите нагрузочные проверки публичного бота. Воспроизводите проблему на своей локальной копии с отдельным тестовым токеном.

## Для владельца бота

- Храните токен только в локальном `.env` или переменных окружения сервера.
- При утечке сначала отзовите токен через BotFather; удаление файла из текущей версии не убирает его из истории.
- Проверяйте зависимости: `python -m pip_audit --local --skip-editable` из `.venv` с dev-зависимостями.
- Перед публикацией выполняйте `python scripts/check_publication.py --history`. Проверка охватывает рабочие файлы, индекс и все локальные Git refs, но не удалённые Actions-логи, артефакты, Issues или неизвестные форматы секретов.

Антифлуд и лимиты задач работают в памяти одного процесса и сбрасываются при перезапуске. Они ограничивают нагрузку на приложение, но не гарантируют доступность при любой атаке. Бот использует long polling; для запуска не нужны webhook, открытый HTTP-порт или Redis.
