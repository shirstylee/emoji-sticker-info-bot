![Emoji & Sticker Info Bot](Images/readme-cover.png)

# 🙂 Emoji & Sticker Info Bot

Telegram-бот для получения и обратного поиска ID обычных и Premium emoji, стикеров и целых паков. Бот умеет обрабатывать отдельные элементы, ссылки на паки и готовые идентификаторы, а результат можно детально настроить и экспортировать в TXT.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](tests)

> Бот в Telegram: [@emoji_info_bot](https://t.me/emoji_info_bot)

## 🚀 Возможности

- получение `custom_emoji_id` для Premium/custom emoji;
- получение Unicode-кода для обычных emoji, например `U+1F34F`;
- получение `file_id` и `file_unique_id` обычных и Premium-стикеров;
- обработка ссылок `t.me/addemoji/...` и `t.me/addstickers/...`;
- вывод всех доступных ID из больших emoji- и sticker-паков;
- обратный поиск Premium emoji по `custom_emoji_id`;
- отображение обычного emoji по Unicode-коду;
- отправка стикера по его `file_id`;
- удаление повторов и автоматическое разделение длинных результатов;
- нативная кнопка копирования одиночного ID;
- экспорт полного результата в TXT;
- русский и английский интерфейс;
- Premium emoji в сообщениях и inline-кнопках с автоматическим fallback-режимом.

## 🔄 Что можно отправить

| Входные данные | Что вернёт бот |
|---|---|
| Обычный emoji | Unicode-код |
| Premium/custom emoji | `custom_emoji_id` |
| Стикер | `file_id`, `file_unique_id` и технические данные |
| Ссылка на emoji-пак | ID всех элементов пака |
| Ссылка на sticker-пак | ID всех стикеров пака |
| `custom_emoji_id` | Соответствующий Premium emoji |
| Unicode вида `U+1F34F` | Соответствующий обычный emoji |
| `file_id` стикера | Сам стикер |

> `file_unique_id` подходит для сравнения файлов, но по нему нельзя повторно отправить или скачать стикер.

## ⚙️ Настройки результата

Настройки сохраняются отдельно для каждого пользователя. Можно изменить:

- Premium emoji, обычный fallback или оба варианта одновременно;
- ID в квадратных скобках, моноширинным кодом или без оформления;
- нумерацию, маркированный список или строки без префикса;
- пробел, тире или перенос строки между элементом и ID;
- пробел после маркера, вокруг тире и между двумя вариантами emoji;
- вывод `file_id`, `file_unique_id` или обоих значений;
- технические данные стикеров;
- заголовок и ссылку на исходный пак;
- удаление повторов;
- Premium-иконки inline-кнопок;
- русский или английский язык интерфейса.

## 🛠️ Стек

- Python 3.11+;
- aiogram 3;
- aiosqlite и SQLite;
- emoji;
- python-dotenv;
- pytest и pytest-asyncio.

## ⚡ Быстрый запуск

### 1. 📥 Клонирование

```bash
git clone https://github.com/YOUR_USERNAME/emoji-sticker-info-bot.git
cd emoji-sticker-info-bot
```

Замените `YOUR_USERNAME` на имя своего аккаунта GitHub.

### 2. 🐍 Установка на Windows

Все зависимости устанавливаются только в локальное окружение `.venv` внутри проекта:

```powershell
.\setup.ps1
```

Скрипт создаст `.venv`, установит проект с dev-зависимостями и подготовит `.env`, если его ещё нет.

### 3. 🔑 Настройка окружения

Получите токен у [@BotFather](https://t.me/BotFather) и заполните `.env`:

```dotenv
BOT_TOKEN=your_bot_token
DB_PATH=data/bot.db
LOG_LEVEL=INFO
```

Файл `.env` содержит секретный токен, исключён из Git и не должен публиковаться.

### 4. ▶️ Запуск

```powershell
.\run.ps1
```

Или напрямую через Python из локального окружения:

```powershell
.\.venv\Scripts\python.exe -m emoji_id_bot.main
```

### Linux и macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
python -m emoji_id_bot.main
```

## 🤖 Команды

- `/start` — главное меню или первоначальный выбор языка;
- `/settings` — настройки результата и интерфейса;
- `/help` — инструкция и примеры входных данных.

## 🗂️ Структура проекта

```text
Emoji & Sticker Info Bot/
├── emoji_id_bot/
│   ├── config.py       # переменные окружения
│   ├── db.py           # SQLite и настройки пользователей
│   ├── exports.py      # подготовка TXT-экспорта
│   ├── extractors.py   # emoji, ID и ссылки на паки
│   ├── formatters.py   # оформление и разбиение результатов
│   ├── handlers.py     # сообщения, команды и callback-кнопки
│   ├── i18n.py         # русский и английский переводы
│   ├── icons.py        # ID Premium emoji интерфейса
│   ├── keyboards.py    # inline-клавиатуры
│   ├── main.py         # запуск polling
│   ├── models.py       # модели данных и настроек
│   └── texts.py        # тексты экранов
├── Images/
│   └── readme-cover.png
├── tests/              # автоматические тесты
├── data/               # локальная SQLite-база, не публикуется
├── .env.example
├── .gitattributes
├── .gitignore
├── GITHUB_SETUP.md
├── pyproject.toml
├── run.ps1
├── setup.ps1
└── README.md
```

## ✅ Проверка

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

## 💾 Хранение данных

- язык и настройки пользователей сохраняются в локальной SQLite-базе;
- отправленные emoji, стикеры, ID и ссылки не записываются в базу;
- TXT-экспорт временно хранится в оперативной памяти и доступен только запросившему пользователю;
- `.env`, `.venv`, локальная база, кэши и логи исключены из Git.

## 🔒 Безопасность

- никогда не публикуйте `.env` и токен BotFather;
- перед каждым коммитом проверяйте файлы командой `git status`;
- если токен попал в Git, сразу отзовите его через BotFather и создайте новый;
- не добавляйте локальную базу `data/bot.db` в репозиторий;
- подробная инструкция первой публикации находится в [`GITHUB_SETUP.md`](GITHUB_SETUP.md).

