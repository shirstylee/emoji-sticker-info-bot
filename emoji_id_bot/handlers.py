from __future__ import annotations

import logging
from dataclasses import replace
from typing import Callable

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message, User
from aiogram.utils.chat_action import ChatActionSender

from . import icons
from .db import Database
from .extractors import (
    deduplicate_emoji_items,
    extract_emoji_items,
    extract_pack_links,
    extract_telegram_ids,
    extract_unicode_id_items,
)
from .exports import ExportStore, html_lines_to_text, safe_export_filename
from .formatters import (
    chunk_line_variants,
    format_emoji_lines,
    format_sticker_lines,
    pack_header,
    sticker_from_telegram,
    strip_custom_emoji_tags,
)
from .i18n import language_code, tr
from .keyboards import (
    appearance_keyboard,
    back_keyboard,
    admin_keyboard,
    admins_keyboard,
    admin_confirm_keyboard,
    main_keyboard,
    pack_settings_keyboard,
    reset_keyboard,
    result_keyboard,
    settings_keyboard,
    sticker_settings_keyboard,
)
from .models import (
    DISPLAY_MODES,
    ID_STYLES,
    PREFIX_STYLES,
    SEPARATORS,
    STICKER_ID_MODES,
    EmojiItem,
    StickerItem,
    ResultSettings,
)
from .security import JobAccess, RequestProtection, SecurityMiddleware
from .texts import (
    admin_text,
    admins_text,
    admin_prompt_text,
    admin_confirm_text,
    about_text,
    appearance_text,
    examples_text,
    help_text,
    main_text,
    pack_settings_text,
    reset_text,
    settings_text,
    sticker_settings_text,
)


logger = logging.getLogger(__name__)
router = Router(name=__name__)
_security_middleware = SecurityMiddleware()
router.message.outer_middleware(_security_middleware)
router.callback_query.outer_middleware(_security_middleware)

KeyboardBuilder = Callable[[bool], InlineKeyboardMarkup]


async def _answer_job_rejected(
    message: Message,
    settings: ResultSettings,
    access: JobAccess,
) -> None:
    if access.reason == "user_busy":
        key = "request_in_progress"
        values: dict[str, object] = {}
    elif access.reason == "pack_cooldown":
        key = "pack_cooldown"
        values = {"seconds": access.retry_after}
    else:
        key = "bot_busy"
        values = {}
    await message.answer(tr(settings.language, key, **values))


class AdminInput(StatesGroup):
    telegram_id = State()


async def _is_admin(db: Database, user_id: int, admin_ids: frozenset[int]) -> bool:
    return user_id in admin_ids or await db.is_admin(user_id)


async def _get_settings(db: Database, user: User, admin_ids: frozenset[int]) -> ResultSettings:
    return replace(
        await db.get_settings(),
        language=language_code(getattr(user, "language_code", None)),
        is_admin=await _is_admin(db, user.id, admin_ids),
    )


async def _disable_icons(db: Database, settings: ResultSettings) -> ResultSettings:
    # A Telegram rendering fallback must not change the shared configuration.
    settings.button_icons = False
    return settings


async def _answer_menu(
    message: Message,
    text: str,
    builder: KeyboardBuilder,
    settings: ResultSettings,
    db: Database,
) -> None:
    try:
        await message.answer(text, reply_markup=builder(settings.button_icons or settings.is_admin))
    except TelegramBadRequest:
        if settings.button_icons:
            try:
                await message.answer(text, reply_markup=builder(False))
                await _disable_icons(db, settings)
                return
            except TelegramBadRequest:
                pass
        fallback_text = strip_custom_emoji_tags(text)
        await message.answer(fallback_text, reply_markup=builder(False))
        await _disable_icons(db, settings)


async def _edit_menu(
    callback: CallbackQuery,
    text: str,
    builder: KeyboardBuilder,
    settings: ResultSettings,
    db: Database,
) -> None:
    message = callback.message
    if not isinstance(message, Message):
        return
    try:
        await message.edit_text(text, reply_markup=builder(settings.button_icons or settings.is_admin))
    except TelegramBadRequest as error:
        if "message is not modified" in str(error).lower():
            return
        if settings.button_icons:
            try:
                await message.edit_text(text, reply_markup=builder(False))
                await _disable_icons(db, settings)
                return
            except TelegramBadRequest as no_icons_error:
                if "message is not modified" in str(no_icons_error).lower():
                    return
        fallback_text = strip_custom_emoji_tags(text)
        await message.edit_text(fallback_text, reply_markup=builder(False))
        await _disable_icons(db, settings)


def _copy_id(sticker: StickerItem, settings: ResultSettings) -> str:
    if sticker.custom_emoji_id:
        return sticker.custom_emoji_id
    if settings.sticker_id_mode == "unique":
        return sticker.file_unique_id
    return sticker.file_id


async def _send_chunks(
    message: Message,
    preferred_lines: list[str],
    standard_lines: list[str],
    settings: ResultSettings,
    db: Database,
    *,
    copy_value: str | None = None,
    export_token: str | None = None,
) -> None:
    preferred_chunks, fallback_chunks = chunk_line_variants(preferred_lines, standard_lines)
    standard_chunks = fallback_chunks
    use_standard = settings.display_mode == "standard"

    # Probe custom-emoji formatting before sending a long multi-part result.
    if len(preferred_chunks) > 1 and not use_standard:
        try:
            await message.answer(preferred_chunks[0])
        except TelegramBadRequest:
            use_standard = True
            await message.answer(fallback_chunks[0])
        start_index = 1
    else:
        start_index = 0

    chunks = standard_chunks if settings.display_mode == "standard" else (
        fallback_chunks if use_standard else preferred_chunks
    )
    for index in range(start_index, len(chunks)):
        is_last = index == len(chunks) - 1
        markup = (
            result_keyboard(
                settings.button_icons,
                copy_value if is_last else None,
                export_token if is_last else None,
                settings.language,
                is_admin=settings.is_admin,
            )
            if is_last
            else None
        )
        try:
            await message.answer(chunks[index], reply_markup=markup)
        except TelegramBadRequest:
            if markup is not None and settings.button_icons:
                try:
                    await message.answer(
                        chunks[index],
                        reply_markup=result_keyboard(
                            False,
                            copy_value if is_last else None,
                            export_token if is_last else None,
                            settings.language,
                            is_admin=settings.is_admin,
                        ),
                    )
                    settings = await _disable_icons(db, settings)
                    continue
                except TelegramBadRequest:
                    pass
            if not use_standard and index < len(fallback_chunks):
                await message.answer(
                    fallback_chunks[index],
                    reply_markup=result_keyboard(
                        False,
                        copy_value if is_last else None,
                        export_token if is_last else None,
                        settings.language,
                        is_admin=settings.is_admin,
                    )
                    if is_last
                    else None,
                )
                settings = await _disable_icons(db, settings)
                use_standard = True
                chunks = fallback_chunks
                continue
            raise


@router.message(CommandStart())
async def command_start(message: Message, db: Database, state: FSMContext,
                        admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None:
        return
    await state.clear()
    settings = await _get_settings(db, message.from_user, admin_ids)
    await _answer_menu(
        message,
        main_text(settings.language),
        lambda use_icons: main_keyboard(use_icons, settings.language, is_admin=settings.is_admin),
        settings,
        db,
    )


@router.message(Command("help"))
async def command_help(message: Message, db: Database, state: FSMContext,
                       admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None:
        return
    await state.clear()
    settings = await _get_settings(db, message.from_user, admin_ids)
    await _answer_menu(
        message,
        help_text(settings.language),
        lambda use_icons: back_keyboard(use_icons, language=settings.language),
        settings,
        db,
    )


@router.message(Command("admin", "settings"))
async def command_admin(message: Message, db: Database, state: FSMContext,
                        admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None:
        return
    await state.clear()
    if message.chat.type != ChatType.PRIVATE or not await _is_admin(db, message.from_user.id, admin_ids):
        await message.answer(tr(message.from_user.language_code, "admin_only"))
        return
    settings = await _get_settings(db, message.from_user, admin_ids)
    await _answer_menu(
        message,
        admin_text(settings.language),
        lambda use_icons: admin_keyboard(use_icons, settings.language),
        settings,
        db,
    )


@router.callback_query()
async def callbacks(callback: CallbackQuery, db: Database, exports: ExportStore,
                    state: FSMContext, admin_ids: frozenset[int] = frozenset()) -> None:
    if callback.from_user is None or not callback.data:
        return
    user_id = callback.from_user.id
    data = callback.data
    if (not isinstance(callback.message, Message)
            or callback.message.chat.type != ChatType.PRIVATE
            or callback.message.chat.id != user_id):
        await callback.answer(tr(callback.from_user.language_code, "private_only"), show_alert=True)
        return
    public = data in {"menu:main", "menu:help", "menu:examples", "menu:about"} or data.startswith("export:")
    if not public and not await _is_admin(db, user_id, admin_ids):
        await state.clear()
        await callback.answer(tr(callback.from_user.language_code, "admin_only"), show_alert=True)
        return
    settings = await _get_settings(db, callback.from_user, admin_ids)
    await state.clear()

    if data.startswith("export:"):
        item = exports.get(data.split(":", 1)[1], user_id)
        if item is None:
            await callback.answer(
                tr(settings.language, "export_expired"),
                show_alert=True,
            )
            return
        if isinstance(callback.message, Message):
            payload = b"\xef\xbb\xbf" + item.content.encode("utf-8")
            await callback.message.answer_document(
                BufferedInputFile(payload, filename=item.filename),
                caption=(
                    f"{icons.tag(icons.DOWNLOAD, '⬇️')} "
                    f"{tr(settings.language, 'export_caption', filename=item.filename)}"
                ),
            )
        await callback.answer(tr(settings.language, "export_ready"))
        return

    language = settings.language
    notice: str | None = None

    try:
        if data == "admin:main":
            await _edit_menu(callback, admin_text(language),
                             lambda use_icons: admin_keyboard(use_icons, language), settings, db)
        elif data == "admin:list":
            extra = await db.list_admins()
            await _edit_menu(callback, admins_text(admin_ids, extra, language),
                             lambda use_icons: admins_keyboard(admin_ids, extra, use_icons, language), settings, db)
        elif data == "admin:add":
            await _edit_menu(callback, admin_prompt_text(language),
                             lambda use_icons: back_keyboard(use_icons, "admins", language), settings, db)
            await state.set_state(AdminInput.telegram_id)
        elif data.startswith(("admin:confirm_add:", "admin:remove:", "admin:confirm_remove:")):
            action, raw_id = data.rsplit(":", 1)
            if (action not in {"admin:confirm_add", "admin:remove", "admin:confirm_remove"}
                    or not raw_id.isascii() or not raw_id.isdigit() or not 0 < int(raw_id) < 2**52):
                notice = tr(language, "unknown_setting")
                return
            target_id = int(raw_id)
            if target_id in admin_ids:
                notice = tr(language, "protected_admin")
                return
            if action == "admin:remove":
                await _edit_menu(callback, admin_confirm_text(target_id, "remove", language),
                                 lambda use_icons: admin_confirm_keyboard(target_id, "remove", use_icons, language), settings, db)
            else:
                if action == "admin:confirm_add":
                    try:
                        added = await db.add_admin(target_id)
                    except ValueError:
                        notice = tr(language, "admin_limit")
                        return
                    notice = tr(language, "admin_added" if added else "admin_exists")
                else:
                    await db.remove_admin(target_id)
                    notice = tr(language, "admin_removed")
                if not await _is_admin(db, user_id, admin_ids):
                    await _edit_menu(callback, main_text(language),
                                     lambda use_icons: main_keyboard(use_icons, language), settings, db)
                else:
                    extra = await db.list_admins()
                    await _edit_menu(callback, admins_text(admin_ids, extra, language),
                                     lambda use_icons: admins_keyboard(admin_ids, extra, use_icons, language), settings, db)
        elif data == "menu:main":
            await _edit_menu(
                callback,
                main_text(language),
                lambda use_icons: main_keyboard(use_icons, language, is_admin=settings.is_admin),
                settings,
                db,
            )
        elif data == "menu:help":
            await _edit_menu(
                callback,
                help_text(language),
                lambda use_icons: back_keyboard(use_icons, language=language),
                settings,
                db,
            )
        elif data == "menu:examples":
            await _edit_menu(
                callback,
                examples_text(language),
                lambda use_icons: back_keyboard(use_icons, language=language),
                settings,
                db,
            )
        elif data == "menu:about":
            await _edit_menu(
                callback,
                about_text(language),
                lambda use_icons: back_keyboard(use_icons, language=language),
                settings,
                db,
            )
        elif data == "menu:settings":
            await _edit_menu(
                callback,
                settings_text(settings),
                lambda icons: settings_keyboard(settings, icons),
                settings,
                db,
            )
        elif data == "settings:appearance":
            await _edit_menu(
                callback,
                appearance_text(settings),
                lambda icons: appearance_keyboard(settings, icons),
                settings,
                db,
            )
        elif data == "settings:stickers":
            await _edit_menu(
                callback,
                sticker_settings_text(language),
                lambda icons: sticker_settings_keyboard(settings, icons),
                settings,
                db,
            )
        elif data == "settings:packs":
            await _edit_menu(
                callback,
                pack_settings_text(language),
                lambda icons: pack_settings_keyboard(settings, icons),
                settings,
                db,
            )
        elif data == "settings:reset":
            await _edit_menu(
                callback,
                reset_text(language),
                lambda use_icons: reset_keyboard(use_icons, language),
                settings,
                db,
            )
        elif data == "settings:reset_confirm":
            settings = replace(await db.reset(), language=language, is_admin=True)
            notice = tr(language, "settings_reset")
            await _edit_menu(
                callback,
                settings_text(settings),
                lambda icons: settings_keyboard(settings, icons),
                settings,
                db,
            )
        elif data.startswith("set:"):
            if len(data.split(":")) != 3:
                notice = tr(language, "unknown_setting")
                return
            _, key, value = data.split(":", 2)
            allowed = {
                "display_mode": DISPLAY_MODES,
                "id_style": ID_STYLES,
                "prefix_style": PREFIX_STYLES,
                "separator": SEPARATORS,
                "sticker_id_mode": STICKER_ID_MODES,
            }
            if key not in allowed or value not in allowed[key]:
                await callback.answer(tr(language, "unknown_setting"), show_alert=True)
                return
            settings = replace(await db.set_value(key, value), language=language, is_admin=True)
            if key in {"display_mode", "id_style", "prefix_style", "separator"}:
                await _edit_menu(
                    callback,
                    appearance_text(settings),
                    lambda icons: appearance_keyboard(settings, icons),
                    settings,
                    db,
                )
            else:
                await _edit_menu(
                    callback,
                    sticker_settings_text(language),
                    lambda icons: sticker_settings_keyboard(settings, icons),
                    settings,
                    db,
                )
        elif data.startswith("toggle:"):
            key = data.split(":", 1)[1]
            if key not in {
                "show_pack_title",
                "show_pack_link",
                "show_details",
                "deduplicate",
                "button_icons",
                "space_after_prefix",
                "spaces_around_dash",
                "space_between_variants",
            }:
                await callback.answer(tr(language, "unknown_setting"), show_alert=True)
                return
            settings = replace(await db.toggle(key), language=language, is_admin=True)
            if key in {
                "space_after_prefix",
                "spaces_around_dash",
                "space_between_variants",
            }:
                await _edit_menu(
                    callback,
                    appearance_text(settings),
                    lambda icons: appearance_keyboard(settings, icons),
                    settings,
                    db,
                )
            elif key == "show_details":
                await _edit_menu(
                    callback,
                    sticker_settings_text(language),
                    lambda icons: sticker_settings_keyboard(settings, icons),
                    settings,
                    db,
                )
            else:
                await _edit_menu(
                    callback,
                    pack_settings_text(language),
                    lambda icons: pack_settings_keyboard(settings, icons),
                    settings,
                    db,
                )
        else:
            await callback.answer(tr(language, "stale_button"), show_alert=True)
            return
    finally:
        try:
            await callback.answer(notice)
        except TelegramBadRequest:
            pass


@router.message(Command("cancel"))
async def cancel_admin_input(message: Message, db: Database, state: FSMContext,
                             admin_ids: frozenset[int] = frozenset()) -> None:
    await state.clear()
    await command_start(message, db, state, admin_ids)


@router.message(AdminInput.telegram_id)
async def receive_admin_id(message: Message, db: Database, state: FSMContext,
                           admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None:
        return
    language = language_code(message.from_user.language_code)
    if message.chat.type != ChatType.PRIVATE or not await _is_admin(db, message.from_user.id, admin_ids):
        await state.clear()
        await message.answer(tr(language, "admin_only"))
        return
    raw_id = (message.text or "").strip()
    if not raw_id.isascii() or not raw_id.isdigit() or not 0 < int(raw_id) < 2**52:
        settings = await _get_settings(db, message.from_user, admin_ids)
        await _answer_menu(message, admin_prompt_text(language),
                           lambda use_icons: back_keyboard(use_icons, "admins", language), settings, db)
        return
    target_id = int(raw_id)
    if await _is_admin(db, target_id, admin_ids):
        settings = await _get_settings(db, message.from_user, admin_ids)
        await _answer_menu(
            message,
            f"{icons.tag(icons.INFO, 'ℹ️')} <blockquote>{tr(language, 'admin_exists')}</blockquote>",
            lambda use_icons: back_keyboard(use_icons, "admins", language), settings, db,
        )
        return
    await state.clear()
    settings = await _get_settings(db, message.from_user, admin_ids)
    await _answer_menu(message, admin_confirm_text(target_id, "add", language),
                       lambda use_icons: admin_confirm_keyboard(target_id, "add", use_icons, language), settings, db)


@router.message(F.sticker)
async def handle_sticker(message: Message, db: Database, exports: ExportStore,
                         admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None or message.sticker is None:
        return
    settings = await _get_settings(db, message.from_user, admin_ids)
    sticker = sticker_from_telegram(message.sticker)
    standard = replace(settings, display_mode="standard")
    preferred_lines = format_sticker_lines([sticker], settings, compact=False)
    standard_lines = format_sticker_lines([sticker], standard, compact=False)
    export_token = exports.put(
        message.from_user.id,
        "sticker_id.txt",
        html_lines_to_text(standard_lines),
    )
    await _send_chunks(
        message,
        preferred_lines,
        standard_lines,
        settings,
        db,
        copy_value=_copy_id(sticker, settings),
        export_token=export_token,
    )


def _deduplicate_stickers(stickers: list[StickerItem]) -> list[StickerItem]:
    result: list[StickerItem] = []
    seen: set[str] = set()
    for sticker in stickers:
        key = sticker.custom_emoji_id or sticker.file_unique_id
        if key not in seen:
            seen.add(key)
            result.append(sticker)
    return result


async def _handle_pack_links(
    message: Message,
    bot: Bot,
    db: Database,
    exports: ExportStore,
    settings: ResultSettings,
    text: str,
) -> bool:
    links = extract_pack_links(text)
    if not links:
        return False
    if len(links) > 5:
        await message.answer(tr(settings.language, "max_links"))
        links = links[:5]

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        for link in links:
            try:
                pack = await bot.get_sticker_set(link.name)
            except TelegramBadRequest:
                await message.answer(
                    tr(settings.language, "pack_failed", name=link.name)
                )
                continue

            stickers = [sticker_from_telegram(item) for item in pack.stickers]
            if settings.deduplicate:
                stickers = _deduplicate_stickers(stickers)
            standard = replace(settings, display_mode="standard")
            header = pack_header(
                pack.title,
                len(stickers),
                pack.sticker_type,
                link.canonical_url,
                settings,
            )
            standard_header = pack_header(
                pack.title,
                len(stickers),
                pack.sticker_type,
                link.canonical_url,
                standard,
            )
            preferred_lines = header + format_sticker_lines(stickers, settings, compact=True)
            standard_lines = standard_header + format_sticker_lines(
                stickers, standard, compact=True
            )
            export_token = exports.put(
                message.from_user.id,
                safe_export_filename(f"{pack.name}_ids"),
                html_lines_to_text(standard_lines),
            )
            await _send_chunks(
                message,
                preferred_lines,
                standard_lines,
                settings,
                db,
                export_token=export_token,
            )
    return True


async def _fetch_custom_emoji_stickers(bot: Bot, custom_ids: list[str]) -> list[object]:
    unique_ids = list(dict.fromkeys(custom_ids))
    stickers: list[object] = []
    for start in range(0, len(unique_ids), 200):
        try:
            stickers.extend(
                await bot.get_custom_emoji_stickers(
                    custom_emoji_ids=unique_ids[start : start + 200]
                )
            )
        except TelegramBadRequest:
            logger.warning("Could not enrich a custom emoji batch", exc_info=True)
    return stickers


async def _enrich_custom_emoji(bot: Bot, items: list[EmojiItem]) -> list[EmojiItem]:
    custom_ids = [item.identifier for item in items if item.kind == "custom"]
    if not custom_ids:
        return items
    unique_ids = list(dict.fromkeys(custom_ids))
    stickers = await _fetch_custom_emoji_stickers(bot, unique_ids)
    by_id = {
        sticker.custom_emoji_id: sticker
        for sticker in stickers
        if getattr(sticker, "custom_emoji_id", None)
    }
    enriched: list[EmojiItem] = []
    for item in items:
        sticker = by_id.get(item.identifier)
        if item.kind == "custom" and sticker is not None:
            enriched.append(
                EmojiItem(
                    kind=item.kind,
                    value=sticker.emoji or item.value,
                    identifier=item.identifier,
                    position=item.position,
                    set_name=sticker.set_name,
                )
            )
        else:
            enriched.append(item)
    return enriched


async def _handle_id_lookup(
    message: Message,
    bot: Bot,
    db: Database,
    exports: ExportStore,
    settings: ResultSettings,
    text: str,
) -> bool:
    identifiers = extract_telegram_ids(text)
    unicode_items = extract_unicode_id_items(text)
    if not identifiers and not unicode_items:
        return False

    custom_ids = [identifier for identifier in identifiers if identifier.isdigit()]
    file_ids = [identifier for identifier in identifiers if not identifier.isdigit()]
    resolved_custom: list[EmojiItem] = []
    unresolved_count = 0

    if custom_ids:
        stickers = await _fetch_custom_emoji_stickers(bot, custom_ids)
        by_id = {
            sticker.custom_emoji_id: sticker
            for sticker in stickers
            if getattr(sticker, "custom_emoji_id", None)
        }
        for index, identifier in enumerate(custom_ids):
            sticker = by_id.get(identifier)
            if sticker is None:
                unresolved_count += 1
            else:
                resolved_custom.append(
                    EmojiItem(
                        kind="custom",
                        value=getattr(sticker, "emoji", None) or "⭐",
                        identifier=identifier,
                        position=index,
                        set_name=getattr(sticker, "set_name", None),
                    )
                )

    emoji_items = unicode_items + resolved_custom
    if emoji_items:
        # Reverse lookup previews the requested asset, not just its fallback glyph.
        if resolved_custom and settings.display_mode == "standard":
            settings = replace(settings, display_mode="custom")
        standard = replace(settings, display_mode="standard")
        preferred_lines = format_emoji_lines(emoji_items, settings)
        standard_lines = format_emoji_lines(emoji_items, standard)
        export_token = exports.put(
            message.from_user.id,
            "resolved_emoji_ids.txt",
            html_lines_to_text(standard_lines),
        )
        await _send_chunks(
            message,
            preferred_lines,
            standard_lines,
            settings,
            db,
            copy_value=emoji_items[0].identifier if len(emoji_items) == 1 else None,
            export_token=export_token,
        )

    if len(file_ids) > 20:
        await message.answer(tr(settings.language, "file_id_limit"))
    for identifier in file_ids[:20]:
        try:
            await message.answer_sticker(sticker=identifier)
        except TelegramBadRequest:
            unresolved_count += 1

    if unresolved_count:
        await message.answer(
            f"{icons.tag(icons.WARNING, '❗️')} "
            f"{tr(settings.language, 'id_lookup_failed', count=unresolved_count)}"
        )
    return True


@router.message(F.text | F.caption)
async def handle_text(
    message: Message,
    bot: Bot,
    db: Database,
    exports: ExportStore,
    protection: RequestProtection,
    admin_ids: frozenset[int] = frozenset(),
) -> None:
    if message.from_user is None:
        return
    text = message.text or message.caption or ""
    settings = await _get_settings(db, message.from_user, admin_ids)
    is_pack = bool(extract_pack_links(text))
    async with protection.job(message.from_user.id, is_pack=is_pack) as access:
        if not access.allowed:
            await _answer_job_rejected(message, settings, access)
            return
        if await _handle_pack_links(message, bot, db, exports, settings, text):
            return
        if await _handle_id_lookup(message, bot, db, exports, settings, text):
            return

        entities = message.entities if message.text is not None else message.caption_entities
        items = extract_emoji_items(text, entities)
        items = await _enrich_custom_emoji(bot, items)
        if settings.deduplicate:
            items = deduplicate_emoji_items(items)
        if not items:
            await message.answer(tr(settings.language, "not_found"))
            return

        standard = replace(settings, display_mode="standard")
        copy_value = items[0].identifier if len(items) == 1 else None
        preferred_lines = format_emoji_lines(items, settings)
        standard_lines = format_emoji_lines(items, standard)
        export_token = exports.put(
            message.from_user.id,
            "emoji_ids.txt",
            html_lines_to_text(standard_lines),
        )
        await _send_chunks(
            message,
            preferred_lines,
            standard_lines,
            settings,
            db,
            copy_value=copy_value,
            export_token=export_token,
        )


@router.message(F.chat.type == ChatType.PRIVATE)
async def unsupported_private_message(message: Message, db: Database,
                                       admin_ids: frozenset[int] = frozenset()) -> None:
    if message.from_user is None:
        return
    settings = await _get_settings(db, message.from_user, admin_ids)
    await message.answer(tr(settings.language, "unsupported"))
