from __future__ import annotations

from functools import wraps

from . import icons
from .i18n import language_code, tr
from .models import ResultSettings


def _state_icon(value: bool) -> str:
    return icons.tag(icons.CONFIRM, "✅") if value else icons.tag(icons.CANCEL, "❌")


def _admin_page(function):
    @wraps(function)
    def quoted(*args, **kwargs):
        heading, body = function(*args, **kwargs).split("\n\n", 1)
        blocks = "\n\n".join(f"<blockquote>{section}</blockquote>" for section in body.split("\n\n"))
        return f"{heading}\n\n{blocks}"
    return quoted


@_admin_page
def admin_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.SETTINGS, '⚙️')} <b>Admin panel</b>

{icons.tag(icons.SLIDERS, '🎛')} <b>Result settings</b>
Set a shared format for all new bot results.

{icons.tag(icons.BOT, '🤖')} <b>Administrators</b>
Grant or revoke access to this panel. Each administrator can manage formatting and other administrators."""
    return f"""{icons.tag(icons.SETTINGS, '⚙️')} <b>Админ-панель</b>

{icons.tag(icons.SLIDERS, '🎛')} <b>Настройки результата</b>
Задайте единый формат для всех новых ответов бота.

{icons.tag(icons.BOT, '🤖')} <b>Администраторы</b>
Выдавайте и отзывайте доступ к панели. Каждый администратор может менять оформление и управлять другими администраторами."""


@_admin_page
def admins_text(roots: frozenset[int], extra: list[int], language: str | None) -> str:
    root_lines = "\n".join(f"<code>{value}</code>" for value in sorted(roots))
    extra_lines = "\n".join(f"<code>{value}</code>" for value in extra if value not in roots) or "—"
    if language_code(language) == "en":
        return f"""{icons.tag(icons.BOT, '🤖')} <b>Administrators</b>

{icons.tag(icons.CONFIRM, '✅')} <b>Protected · .env</b>
{root_lines}

{icons.tag(icons.LIST, '🗂')} <b>Added in this panel</b>
{extra_lines}

{icons.tag(icons.INFO, 'ℹ️')} Use the buttons below to add or remove access. Protected administrators can only be changed in ADMIN_IDS on the server, followed by a restart."""
    return f"""{icons.tag(icons.BOT, '🤖')} <b>Администраторы</b>

{icons.tag(icons.CONFIRM, '✅')} <b>Защищённые · .env</b>
{root_lines}

{icons.tag(icons.LIST, '🗂')} <b>Добавленные через панель</b>
{extra_lines}

{icons.tag(icons.INFO, 'ℹ️')} Кнопками ниже можно выдать или отозвать доступ. Защищённых администраторов можно изменить только в ADMIN_IDS на сервере с последующим перезапуском."""


@_admin_page
def admin_prompt_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.CONFIRM, '✅')} <b>Add administrator</b>

{icons.tag(icons.CODE, '🔨')} Send the numeric Telegram user ID in a separate message. A username or phone number is not suitable.

{icons.tag(icons.INFO, 'ℹ️')} You will confirm access on the next screen. Press Back or send /cancel to cancel. The input session expires in 10 minutes."""
    return f"""{icons.tag(icons.CONFIRM, '✅')} <b>Добавить администратора</b>

{icons.tag(icons.CODE, '🔨')} Отправьте числовой Telegram ID пользователя отдельным сообщением. Никнейм и номер телефона не подходят.

{icons.tag(icons.INFO, 'ℹ️')} На следующем экране нужно подтвердить выдачу доступа. Для отмены нажмите «Назад» или отправьте /cancel. На ввод ID даётся 10 минут."""


@_admin_page
def admin_confirm_text(telegram_id: int, action: str, language: str | None) -> str:
    if language_code(language) == "en":
        title = "Grant administrator access?" if action == "add" else "Revoke administrator access?"
        detail = ("This ID will be able to change the shared format and manage administrators. Check the ID before confirming."
                  if action == "add" else "This ID will lose access to the admin panel. The bot will remain available as usual.")
    else:
        title = "Выдать права администратора?" if action == "add" else "Отозвать права администратора?"
        detail = ("Этот ID сможет менять общий формат и управлять администраторами. Проверьте ID перед подтверждением."
                  if action == "add" else "Этот ID потеряет доступ к админ-панели. Обычные функции бота останутся доступны.")
    return (f"{icons.tag(icons.WARNING, '❗️')} <b>{title}</b>\n\n"
            f"{icons.tag(icons.CODE, '🔨')} Telegram ID: <code>{telegram_id}</code>\n\n"
            f"{icons.tag(icons.INFO, 'ℹ️')} {detail}")


def main_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.BOT, "🤖")} <b>emoji-sticker-info-bot</b>

{icons.tag(icons.COMMAND, "🔣")} <b>Send me:</b>
• a standard or Premium emoji;
• a <code>t.me/addemoji/…</code> link;
• a standard or Premium sticker;
• a <code>t.me/addstickers/…</code> link;
• a <code>custom_emoji_id</code>, Unicode code or sticker <code>file_id</code> to display it.

{icons.tag(icons.SEARCH, "🔎")} I will return every available ID. Standard emoji have no Telegram ID, so their Unicode code will be shown."""
    return f"""{icons.tag(icons.BOT, "🤖")} <b>emoji-sticker-info-bot</b>

{icons.tag(icons.COMMAND, "🔣")} <b>Отправьте мне:</b>
• обычный или Premium emoji;
• ссылку <code>t.me/addemoji/…</code>;
• обычный или Premium-стикер;
• ссылку <code>t.me/addstickers/…</code>;
• <code>custom_emoji_id</code>, Unicode-код или <code>file_id</code> стикера, чтобы показать элемент.

{icons.tag(icons.SEARCH, "🔎")} Я верну ID каждого элемента. Для обычных эмодзи, у которых нет Telegram-ID, будет показан Unicode-код."""


def help_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.HELP, "❓")} <b>How to use</b>

1. Send one or more emoji in a message.
2. Or send the sticker itself.
3. Or paste an emoji/sticker pack link.

{icons.tag(icons.CODE, "🔨")} <b>IDs returned by the bot</b>
• Premium/custom emoji — <code>custom_emoji_id</code>;
• standard emoji — Unicode such as <code>U+1F34F</code>;
• sticker — <code>file_id</code> and/or <code>file_unique_id</code>;
• Premium stickers can also be marked in technical details.

{icons.tag(icons.SEARCH, "🔎")} <b>Display from an ID</b>
• a numeric <code>custom_emoji_id</code> displays the Premium emoji;
• <code>U+1F34F</code> displays a standard emoji;
• sticker <code>file_id</code> sends the sticker itself;
• <code>file_unique_id</code> cannot be used to restore a sticker.

{icons.tag(icons.INFO, "ℹ️")} Large packs are automatically split across multiple messages. Use Export TXT to download the complete result."""
    return f"""{icons.tag(icons.HELP, "❓")} <b>Как пользоваться</b>

1. Отправьте один или несколько эмодзи одним сообщением.
2. Либо пришлите сам стикер.
3. Либо вставьте ссылку на emoji/sticker pack.

{icons.tag(icons.CODE, "🔨")} <b>Какие ID показывает бот</b>
• Premium/custom emoji — <code>custom_emoji_id</code>;
• обычный emoji — Unicode вида <code>U+1F34F</code>;
• стикер — <code>file_id</code> и/или <code>file_unique_id</code>;
• Premium-стикер дополнительно помечается в технических данных.

{icons.tag(icons.SEARCH, "🔎")} <b>Показать элемент по ID</b>
• числовой <code>custom_emoji_id</code> покажет Premium emoji;
• <code>U+1F34F</code> покажет обычный emoji;
• <code>file_id</code> стикера отправит сам стикер;
• восстановить стикер по <code>file_unique_id</code> невозможно.

{icons.tag(icons.INFO, "ℹ️")} Если пак большой, результат автоматически придёт несколькими сообщениями. Кнопка «Экспорт TXT» скачает полный результат."""


def examples_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.ARTICLE, "📝")} <b>Input examples</b>

{icons.tag(icons.PREMIUM, "⭐️")} <b>Emoji:</b>
<code>✈️ 🍏 ⭐️</code>

{icons.tag(icons.LINK, "🔗")} <b>Emoji pack:</b>
<code>https://t.me/addemoji/PackName</code>

{icons.tag(icons.FILE, "📁")} <b>Sticker pack:</b>
<code>https://t.me/addstickers/PackName</code>

{icons.tag(icons.CODE, "🔨")} <b>Display from an ID:</b>
<code>6028346797368283073</code>
<code>U+1F34F</code>
<code>CAACAgIAAxkBAA…</code>

{icons.tag(icons.IMAGE, "🖼")} You can simply forward a sticker to the bot. A Premium emoji must be sent as a custom emoji, not as an image."""
    return f"""{icons.tag(icons.ARTICLE, "📝")} <b>Примеры входных данных</b>

{icons.tag(icons.PREMIUM, "⭐️")} <b>Эмодзи:</b>
<code>✈️ 🍏 ⭐️</code>

{icons.tag(icons.LINK, "🔗")} <b>Emoji pack:</b>
<code>https://t.me/addemoji/PackName</code>

{icons.tag(icons.FILE, "📁")} <b>Sticker pack:</b>
<code>https://t.me/addstickers/PackName</code>

{icons.tag(icons.CODE, "🔨")} <b>Показать по ID:</b>
<code>6028346797368283073</code>
<code>U+1F34F</code>
<code>CAACAgIAAxkBAA…</code>

{icons.tag(icons.IMAGE, "🖼")} Сам стикер можно просто переслать боту. Premium emoji важно отправлять именно как custom emoji, а не как картинку."""


def about_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.INFO, "ℹ️")} <b>About the bot</b>

{icons.tag(icons.SEARCH, "🔎")} The bot quickly finds IDs for standard and Premium emoji, stickers and entire packs.

{icons.tag(icons.PREMIUM, "⭐️")} <b>Features:</b>
• recognize multiple emoji at once;
• process emoji and sticker packs from a link;
• return <code>custom_emoji_id</code>, <code>file_id</code> and <code>file_unique_id</code>;
• display emoji and stickers from their reusable IDs;
• copy IDs and export results.

{icons.tag(icons.DOWNLOAD, "⬇️")} Download any complete result as TXT — especially useful for large packs."""
    return f"""{icons.tag(icons.INFO, "ℹ️")} <b>О боте</b>

{icons.tag(icons.SEARCH, "🔎")} Бот помогает быстро находить ID обычных и Premium emoji, стикеров и целых паков.

{icons.tag(icons.PREMIUM, "⭐️")} <b>Возможности:</b>
• распознавание нескольких emoji за один раз;
• обработка emoji- и sticker-паков по ссылке;
• получение <code>custom_emoji_id</code>, <code>file_id</code> и <code>file_unique_id</code>;
• показ emoji и стикеров по поддерживаемым ID;
• копирование ID и экспорт результатов.

{icons.tag(icons.DOWNLOAD, "⬇️")} После проверки результата его можно целиком скачать в TXT — это особенно удобно для больших паков."""


@_admin_page
def settings_text(settings: ResultSettings) -> str:
    language = language_code(settings.language)
    if language == "en":
        display = {
            "custom": "Premium/custom emoji",
            "standard": "standard emoji",
            "both": "Premium + standard emoji",
        }[settings.display_mode]
        id_style = {
            "brackets": "[ID]",
            "code": "monospace code",
            "plain": "no formatting",
        }[settings.id_style]
        prefix = {"number": "numbering", "bullet": "bullets", "none": "no prefix"}[
            settings.prefix_style
        ]
        separator = {"space": "space", "dash": "dash", "newline": "new line"}[
            settings.separator
        ]
        sticker_ids = {
            "file": "file_id",
            "unique": "file_unique_id",
            "both": "both IDs",
        }[settings.sticker_id_mode]
        return f"""{icons.tag(icons.SETTINGS, "⚙️")} <b>Result settings</b>

{icons.tag(icons.INFO, "ℹ️")} Changes apply to new results for everyone. Previously sent messages and TXT files remain unchanged.

{icons.tag(icons.PREMIUM, "⭐️")} Emoji view: <b>{display}</b>
{icons.tag(icons.CODE, "🔨")} ID formatting: <b>{id_style}</b>
{icons.tag(icons.LIST, "🗂")} List style: <b>{prefix}</b>
{icons.tag(icons.MORE, "➕")} Separator: <b>{separator}</b>
{icons.tag(icons.FILE, "📁")} Sticker ID: <b>{sticker_ids}</b>
{icons.tag(icons.INFO, "ℹ️")} Technical details: {_state_icon(settings.show_details)}
{icons.tag(icons.LINK, "🔗")} Pack title and link: {_state_icon(settings.show_pack_title)} / {_state_icon(settings.show_pack_link)}
{icons.tag(icons.REFRESH, "🔁")} Remove duplicates: {_state_icon(settings.deduplicate)}
{icons.tag(icons.BOT, "🤖")} Premium button icons: {_state_icon(settings.button_icons)}
{icons.tag(icons.MORE, "➕")} Spacing (prefix / dash / variants): {_state_icon(settings.space_after_prefix)} / {_state_icon(settings.spaces_around_dash)} / {_state_icon(settings.space_between_variants)}
""".rstrip()

    display = {
        "custom": "Premium/custom emoji",
        "standard": "обычный emoji",
        "both": "Premium + обычный emoji",
    }[settings.display_mode]
    id_style = {
        "brackets": "[ID]",
        "code": "моноширинный код",
        "plain": "без оформления",
    }[settings.id_style]
    prefix = {"number": "нумерация", "bullet": "маркеры", "none": "без префикса"}[
        settings.prefix_style
    ]
    separator = {"space": "пробел", "dash": "тире", "newline": "новая строка"}[
        settings.separator
    ]
    sticker_ids = {
        "file": "file_id",
        "unique": "file_unique_id",
        "both": "оба ID",
    }[settings.sticker_id_mode]
    return f"""{icons.tag(icons.SETTINGS, "⚙️")} <b>Настройки результата</b>

{icons.tag(icons.INFO, "ℹ️")} Изменения действуют для всех новых результатов. Уже отправленные сообщения и TXT-файлы остаются прежними.

{icons.tag(icons.PREMIUM, "⭐️")} Вид эмодзи: <b>{display}</b>
{icons.tag(icons.CODE, "🔨")} Оформление ID: <b>{id_style}</b>
{icons.tag(icons.LIST, "🗂")} Список: <b>{prefix}</b>
{icons.tag(icons.MORE, "➕")} Разделитель: <b>{separator}</b>
{icons.tag(icons.FILE, "📁")} ID стикера: <b>{sticker_ids}</b>
{icons.tag(icons.INFO, "ℹ️")} Технические данные: {_state_icon(settings.show_details)}
{icons.tag(icons.LINK, "🔗")} Заголовок и ссылка пака: {_state_icon(settings.show_pack_title)} / {_state_icon(settings.show_pack_link)}
{icons.tag(icons.REFRESH, "🔁")} Убирать повторы: {_state_icon(settings.deduplicate)}
{icons.tag(icons.BOT, "🤖")} Premium-иконки кнопок: {_state_icon(settings.button_icons)}
{icons.tag(icons.MORE, "➕")} Пробелы (маркер / тире / варианты): {_state_icon(settings.space_after_prefix)} / {_state_icon(settings.spaces_around_dash)} / {_state_icon(settings.space_between_variants)}
""".rstrip()


@_admin_page
def appearance_text(settings: ResultSettings) -> str:
    language = language_code(settings.language)
    variants_gap = " " if settings.space_between_variants else ""
    visual = {
        "custom": icons.tag(icons.TELEGRAM, "✈️"),
        "standard": "✈️",
        "both": f"{icons.tag(icons.TELEGRAM, '✈️')}{variants_gap}✈️",
    }[settings.display_mode]
    identifier = {
        "brackets": "[6028346797368283073]",
        "code": "<code>6028346797368283073</code>",
        "plain": "6028346797368283073",
    }[settings.id_style]
    prefix = {"number": "1)", "bullet": "•", "none": ""}[settings.prefix_style]
    dash = " - " if settings.spaces_around_dash else "-"
    separator = {"space": " ", "dash": dash, "newline": "\n"}[settings.separator]
    prefix_gap = " " if prefix and settings.space_after_prefix else ""
    if language == "en":
        return (
            f"{icons.tag(icons.SLIDERS, '🎛')} <b>Result appearance</b>\n\n"
            f"{icons.tag(icons.SETTINGS, '⚙️')} Choose the emoji view, ID formatting, line prefix and separator.\n\n"
            f"{icons.tag(icons.ARTICLE, '📝')} <b>Preview:</b>\n"
            f"{prefix}{prefix_gap}{visual}{separator}{identifier}"
        )
    return (
        f"{icons.tag(icons.SLIDERS, '🎛')} <b>Вид результата</b>\n\n"
        f"{icons.tag(icons.SETTINGS, '⚙️')} Настройте отображение эмодзи, ID, префикс строки и разделитель.\n\n"
        f"{icons.tag(icons.ARTICLE, '📝')} <b>Пример:</b>\n"
        f"{prefix}{prefix_gap}{visual}{separator}{identifier}"
    )


@_admin_page
def sticker_settings_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.STICKER, "🙂")} <b>Sticker IDs and details</b>

Choose which identifier to show for standard and Premium stickers:

{icons.tag(icons.FILE, "📁")} <b>file_id</b>
Lets the bot resend or download the sticker. This is the main option for use in code. It belongs to the current bot and may change if the file is uploaded again.

{icons.tag(icons.COPY, "📄")} <b>unique_id</b>
A stable identifier for the same file. Useful for duplicate detection and databases, but it cannot be used to send or download the sticker.

{icons.tag(icons.LIST, "🗂")} <b>Both IDs</b>
Shows <code>file_id</code> for working with the file and <code>file_unique_id</code> for comparison. Results will be longer, especially for large packs.

{icons.tag(icons.PREMIUM, "⭐️")} A custom emoji always shows <code>custom_emoji_id</code> first — this setting does not replace it."""
    return f"""{icons.tag(icons.STICKER, "🙂")} <b>ID и данные стикеров</b>

Выберите, какой идентификатор выводить для обычных и Premium-стикеров:

{icons.tag(icons.FILE, "📁")} <b>file_id</b>
Нужен, чтобы бот мог повторно отправить или скачать стикер. Это основной вариант для использования в коде. ID действует для текущего бота и может измениться после повторной загрузки файла.

{icons.tag(icons.COPY, "📄")} <b>unique_id</b>
Стабильный идентификатор одного и того же файла. Подходит для поиска повторов и хранения в базе, но отправить или скачать стикер по нему нельзя.

{icons.tag(icons.LIST, "🗂")} <b>Оба ID</b>
Бот покажет <code>file_id</code> для работы с файлом и <code>file_unique_id</code> для сравнения. Ответ станет длиннее, особенно для больших паков.

{icons.tag(icons.PREMIUM, "⭐️")} Для custom emoji первым всегда показывается <code>custom_emoji_id</code> — настройка выше его не заменяет."""


@_admin_page
def pack_settings_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.LINK, "🔗")} <b>Packs and interface</b>

{icons.tag(icons.LIST, "🗂")} Configure large-result headings, duplicate removal and Premium icons on inline buttons."""
    return f"""{icons.tag(icons.LINK, "🔗")} <b>Паки и интерфейс</b>

{icons.tag(icons.LIST, "🗂")} Здесь настраиваются заголовки больших результатов, удаление повторяющихся ID и Premium-иконки inline-кнопок."""


@_admin_page
def reset_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.WARNING, "❗️")} <b>Reset settings?</b>

{icons.tag(icons.REFRESH, "🔁")} Restore the default format for everyone: standard emoji - ID, without numbering or brackets. Administrator access remains unchanged."""
    return f"""{icons.tag(icons.WARNING, "❗️")} <b>Сбросить настройки?</b>

{icons.tag(icons.REFRESH, "🔁")} Для всех будет восстановлен формат: обычный emoji - ID, без нумерации и скобок. Права администраторов останутся прежними."""


# Russian aliases retained for tests and external imports.
MAIN_TEXT = main_text("ru")
HELP_TEXT = help_text("ru")
EXAMPLES_TEXT = examples_text("ru")
ABOUT_TEXT = about_text("ru")
STICKER_SETTINGS_TEXT = sticker_settings_text("ru")
PACK_SETTINGS_TEXT = pack_settings_text("ru")
RESET_TEXT = reset_text("ru")
