from __future__ import annotations

from functools import wraps
import html

from . import icons
from .i18n import language_code, tr
from .models import ResultSettings


def _state_icon(value: bool) -> str:
    return icons.tag(icons.CONFIRM, "✅") if value else icons.tag(icons.CANCEL, "❌")


def settings_scope_text(language: str | None, scope: str) -> str:
    if scope == "personal":
        return icons.tag(icons.INFO, 'ℹ️')
    if language_code(language) == "en":
        text = "These settings apply to all users except administrators."
    else:
        text = "Эти настройки действуют для всех пользователей, кроме администраторов."
    return f"{icons.tag(icons.INFO, 'ℹ️')} <b>{text}</b>"


def _quoted_page(function):
    @wraps(function)
    def quoted(*args, **kwargs):
        heading, body = function(*args, **kwargs).split("\n\n", 1)
        # Keep the retained icon with the following text, not in an empty quote.
        info_icon = icons.tag(icons.INFO, 'ℹ️')
        body = body.replace(f"{info_icon}\n\n", f"{info_icon}\n")
        blocks = "\n\n".join(f"<blockquote>{section}</blockquote>" for section in body.split("\n\n"))
        return f"{heading}\n\n{blocks}"
    return quoted


@_quoted_page
def admin_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.SETTINGS, '⚙️')} <b>Admin panel</b>

{icons.tag(icons.SLIDERS, '🎛')} <b>Result settings</b>
Set the result format for regular users only. Your own format is configured in Settings in the main menu.

{icons.tag(icons.BOT, '🤖')} <b>Administrators</b>
Grant or revoke access to this panel. Each administrator can manage formatting and other administrators.

{icons.tag(icons.DOWNLOAD, '⬇️')} <b>Export settings</b>
Download a JSON snapshot of the result format for regular users, excluding personal administrator settings.

{icons.tag(icons.INFO, 'ℹ️')} <b>Bot status</b>
Check uptime, active text jobs, processing limits, cached TXT exports and runtime versions."""
    return f"""{icons.tag(icons.SETTINGS, '⚙️')} <b>Админ-панель</b>

{icons.tag(icons.SLIDERS, '🎛')} <b>Настройки результата</b>
Задайте формат ответов обычным пользователям. Свой формат меняйте в настройках главного меню.

{icons.tag(icons.BOT, '🤖')} <b>Администраторы</b>
Выдавайте и отзывайте доступ к панели. Каждый администратор может менять оформление и управлять другими администраторами.

{icons.tag(icons.DOWNLOAD, '⬇️')} <b>Экспорт настроек</b>
Скачайте в JSON формат для обычных пользователей, без личных настроек администраторов.

{icons.tag(icons.INFO, 'ℹ️')} <b>Состояние бота</b>
Проверьте время работы, активные текстовые запросы, лимиты обработки, TXT-экспорты в кэше и версии среды."""


@_quoted_page
def admin_export_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.DOWNLOAD, '⬇️')} <b>Export settings</b>

{icons.tag(icons.FILE, '📁')} <code>result-settings.json</code> contains the format for regular users: emoji view, ID formatting, spacing, pack options and button icons. Personal administrator settings are not included.

{icons.tag(icons.INFO, 'ℹ️')} Save it to compare settings or reapply them manually later. This is not a full database backup; automatic import is not available. Exporting does not change the bot settings."""
    return f"""{icons.tag(icons.DOWNLOAD, '⬇️')} <b>Экспорт настроек</b>

{icons.tag(icons.FILE, '📁')} В файле <code>result-settings.json</code> — параметры результата для обычных пользователей: вид эмодзи, оформление ID, пробелы, параметры паков и иконок кнопок. Личные настройки администраторов в файл не входят.

{icons.tag(icons.INFO, 'ℹ️')} Сохраните файл для сравнения настроек или их ручного восстановления. Это не полная копия базы; автоматический импорт пока не предусмотрен. Экспорт не меняет настройки бота."""


@_quoted_page
def admin_status_text(language: str | None, *, uptime_seconds: int,
                      admin_count: int, export_count: int,
                      export_limit: int = 500, export_ttl: int = 3600,
                      active_jobs: int | None = None, job_limit: int | None = None,
                      pack_cooldown: float | None = None,
                      python_version: str = "—", aiogram_version: str = "—") -> str:
    hours, remainder = divmod(max(0, uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    jobs = f"{active_jobs} / {job_limit}" if active_jobs is not None and job_limit is not None else "—"
    cooldown = f"{pack_cooldown:g}" if pack_cooldown is not None else "—"
    versions = f"Python <code>{html.escape(python_version)}</code> · aiogram <code>{html.escape(aiogram_version)}</code>"
    if language_code(language) == "en":
        return f"""{icons.tag(icons.INFO, 'ℹ️')} <b>Bot status</b>

{icons.tag(icons.REFRESH, '🔁')} Uptime (hours:minutes:seconds): <code>{uptime}</code>
{icons.tag(icons.BOT, '🤖')} Update mode: <b>Long polling</b>
{icons.tag(icons.CONFIRM, '✅')} Settings database: <b>Readable</b>

{icons.tag(icons.SETTINGS, '⚙️')} Administrators: <b>{admin_count}</b>
{icons.tag(icons.DOWNLOAD, '⬇️')} Cached TXT exports: <b>{export_count} / {export_limit}</b>
{icons.tag(icons.FILE, '📁')} TXT cache lifetime: up to <b>{export_ttl} s</b>

{icons.tag(icons.SLIDERS, '🎛')} Active text jobs / limit: <b>{jobs}</b>
{icons.tag(icons.REFRESH, '🔁')} Per-user pack cooldown: <b>{cooldown} s</b>

{icons.tag(icons.CODE, '🔨')} {versions}

{icons.tag(icons.INFO, 'ℹ️')} Snapshot at the time of opening. Uptime resets when the process restarts."""
    return f"""{icons.tag(icons.INFO, 'ℹ️')} <b>Состояние бота</b>

{icons.tag(icons.REFRESH, '🔁')} Время работы (часы:минуты:секунды): <code>{uptime}</code>
{icons.tag(icons.BOT, '🤖')} Получение обновлений: <b>Long polling</b>
{icons.tag(icons.CONFIRM, '✅')} База настроек: <b>Доступна для чтения</b>

{icons.tag(icons.SETTINGS, '⚙️')} Администраторы: <b>{admin_count}</b>
{icons.tag(icons.DOWNLOAD, '⬇️')} TXT-экспорты в кэше: <b>{export_count} / {export_limit}</b>
{icons.tag(icons.FILE, '📁')} Срок TXT в кэше: до <b>{export_ttl} с</b>

{icons.tag(icons.SLIDERS, '🎛')} Активные текстовые запросы / лимит: <b>{jobs}</b>
{icons.tag(icons.REFRESH, '🔁')} Пауза между паками одного пользователя: <b>{cooldown} с</b>

{icons.tag(icons.CODE, '🔨')} {versions}

{icons.tag(icons.INFO, 'ℹ️')} Данные на момент открытия. Время работы обнуляется при перезапуске процесса."""


@_quoted_page
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


@_quoted_page
def admin_prompt_text(language: str | None) -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.CONFIRM, '✅')} <b>Add administrator</b>

{icons.tag(icons.CODE, '🔨')} Send the numeric Telegram user ID in a separate message. A username or phone number is not suitable.

{icons.tag(icons.INFO, 'ℹ️')} You will confirm access on the next screen. Press Back or send /cancel to cancel. The input session expires in 10 minutes."""
    return f"""{icons.tag(icons.CONFIRM, '✅')} <b>Добавить администратора</b>

{icons.tag(icons.CODE, '🔨')} Отправьте числовой Telegram ID пользователя отдельным сообщением. Никнейм и номер телефона не подходят.

{icons.tag(icons.INFO, 'ℹ️')} На следующем экране нужно подтвердить выдачу доступа. Для отмены нажмите «Назад» или отправьте /cancel. На ввод ID даётся 10 минут."""


@_quoted_page
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
        return f"""{icons.tag(icons.BOT, "🤖")} <b>Emoji &amp; Sticker Info</b>

<blockquote>{icons.tag(icons.COMMAND, "🔣")} <b>Send me:</b>
• a standard or Premium emoji;
• a <code>t.me/addemoji/…</code> link;
• a standard or Premium sticker;
• a <code>t.me/addstickers/…</code> link;
• a <code>custom_emoji_id</code>, Unicode code or sticker <code>file_id</code> to display it.</blockquote>

{icons.tag(icons.SEARCH, "🔎")} I will return every available ID. Standard emoji have no Telegram ID, so their Unicode code will be shown."""
    return f"""{icons.tag(icons.BOT, "🤖")} <b>Emoji &amp; Sticker Info</b>

<blockquote>{icons.tag(icons.COMMAND, "🔣")} <b>Отправьте мне:</b>
• обычный или Premium emoji;
• ссылку <code>t.me/addemoji/…</code>;
• обычный или Premium-стикер;
• ссылку <code>t.me/addstickers/…</code>;
• <code>custom_emoji_id</code>, Unicode-код или <code>file_id</code> стикера, чтобы показать элемент.</blockquote>

{icons.tag(icons.SEARCH, "🔎")} Я верну ID каждого элемента. Для обычных эмодзи, у которых нет Telegram-ID, будет показан Unicode-код."""


@_quoted_page
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


@_quoted_page
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


@_quoted_page
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


@_quoted_page
def settings_text(settings: ResultSettings) -> str:
    language = language_code(settings.language)
    scope_note = settings_scope_text(language, settings.settings_scope)
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

{scope_note}
Changes apply to new results. Previously sent messages and TXT files remain unchanged.

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

{scope_note}
Изменения действуют для новых результатов. Уже отправленные сообщения и TXT-файлы остаются прежними.

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


@_quoted_page
def appearance_text(settings: ResultSettings) -> str:
    language = language_code(settings.language)
    scope_note = settings_scope_text(language, settings.settings_scope)
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
            f"{scope_note}\n\n"
            f"{icons.tag(icons.SETTINGS, '⚙️')} Choose the emoji view, ID formatting, line prefix and separator.\n\n"
            f"{icons.tag(icons.ARTICLE, '📝')} <b>Preview:</b>\n"
            f"{prefix}{prefix_gap}{visual}{separator}{identifier}"
        )
    return (
        f"{icons.tag(icons.SLIDERS, '🎛')} <b>Вид результата</b>\n\n"
        f"{scope_note}\n\n"
        f"{icons.tag(icons.SETTINGS, '⚙️')} Настройте отображение эмодзи, ID, префикс строки и разделитель.\n\n"
        f"{icons.tag(icons.ARTICLE, '📝')} <b>Пример:</b>\n"
        f"{prefix}{prefix_gap}{visual}{separator}{identifier}"
    )


@_quoted_page
def sticker_settings_text(language: str | None, *, scope: str = "global") -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.STICKER, "🙂")} <b>Sticker IDs and details</b>

{settings_scope_text(language, scope)}

Choose which identifier to show for standard and Premium stickers:

{icons.tag(icons.FILE, "📁")} <b>file_id</b>
Lets the bot resend or download the sticker. This is the main option for use in code. It belongs to the current bot and may change if the file is uploaded again.

{icons.tag(icons.COPY, "📄")} <b>unique_id</b>
A stable identifier for the same file. Useful for duplicate detection and databases, but it cannot be used to send or download the sticker.

{icons.tag(icons.LIST, "🗂")} <b>Both IDs</b>
Shows <code>file_id</code> for working with the file and <code>file_unique_id</code> for comparison. Results will be longer, especially for large packs.

{icons.tag(icons.PREMIUM, "⭐️")} A custom emoji always shows <code>custom_emoji_id</code> first — this setting does not replace it."""
    return f"""{icons.tag(icons.STICKER, "🙂")} <b>ID и данные стикеров</b>

{settings_scope_text(language, scope)}

Выберите, какой идентификатор выводить для обычных и Premium-стикеров:

{icons.tag(icons.FILE, "📁")} <b>file_id</b>
Нужен, чтобы бот мог повторно отправить или скачать стикер. Это основной вариант для использования в коде. ID действует для текущего бота и может измениться после повторной загрузки файла.

{icons.tag(icons.COPY, "📄")} <b>unique_id</b>
Стабильный идентификатор одного и того же файла. Подходит для поиска повторов и хранения в базе, но отправить или скачать стикер по нему нельзя.

{icons.tag(icons.LIST, "🗂")} <b>Оба ID</b>
Бот покажет <code>file_id</code> для работы с файлом и <code>file_unique_id</code> для сравнения. Ответ станет длиннее, особенно для больших паков.

{icons.tag(icons.PREMIUM, "⭐️")} Для custom emoji первым всегда показывается <code>custom_emoji_id</code> — настройка выше его не заменяет."""


@_quoted_page
def pack_settings_text(language: str | None, *, scope: str = "global") -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.LINK, "🔗")} <b>Packs and interface</b>

{settings_scope_text(language, scope)}

{icons.tag(icons.LIST, "🗂")} Configure large-result headings, duplicate removal and Premium icons on inline buttons."""
    return f"""{icons.tag(icons.LINK, "🔗")} <b>Паки и интерфейс</b>

{settings_scope_text(language, scope)}

{icons.tag(icons.LIST, "🗂")} Здесь настраиваются заголовки больших результатов, удаление повторяющихся ID и Premium-иконки inline-кнопок."""


@_quoted_page
def reset_text(language: str | None, *, scope: str = "global") -> str:
    if language_code(language) == "en":
        return f"""{icons.tag(icons.WARNING, "❗️")} <b>Reset settings?</b>

{settings_scope_text(language, scope)}

{icons.tag(icons.REFRESH, "🔁")} Restore the default format in this section: standard emoji - ID, without numbering or brackets. Other profiles and administrator access remain unchanged."""
    return f"""{icons.tag(icons.WARNING, "❗️")} <b>Сбросить настройки?</b>

{settings_scope_text(language, scope)}

{icons.tag(icons.REFRESH, "🔁")} В этом разделе будет восстановлен формат: обычный emoji - ID, без нумерации и скобок. Другие профили настроек и права администраторов останутся прежними."""


# Russian aliases retained for tests and external imports.
MAIN_TEXT = main_text("ru")
HELP_TEXT = help_text("ru")
EXAMPLES_TEXT = examples_text("ru")
ABOUT_TEXT = about_text("ru")
STICKER_SETTINGS_TEXT = sticker_settings_text("ru")
PACK_SETTINGS_TEXT = pack_settings_text("ru")
RESET_TEXT = reset_text("ru")
