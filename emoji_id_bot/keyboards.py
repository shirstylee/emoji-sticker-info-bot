from __future__ import annotations

from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup

from . import icons
from .i18n import language_code, tr
from .models import UserSettings


def _button(
    text: str,
    callback_data: str | None,
    icon: str,
    use_icons: bool,
    *,
    style: str | None = None,
    copy_text: str | None = None,
) -> InlineKeyboardButton:
    data: dict[str, object] = {"text": text}
    if callback_data is not None:
        data["callback_data"] = callback_data
    if copy_text is not None:
        data["copy_text"] = CopyTextButton(text=copy_text)
    if use_icons:
        data["icon_custom_emoji_id"] = icon
    if style:
        data["style"] = style
    return InlineKeyboardButton(**data)


def language_keyboard(
    use_icons: bool,
    *,
    current: str | None = None,
    origin: str = "start",
    include_back: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [
            _button(
                ("✓ " if current == "ru" else "") + "Русский",
                f"lang:ru:{origin}",
                icons.RUSSIAN_FLAG,
                use_icons,
                style="primary" if current == "ru" else None,
            ),
            _button(
                ("✓ " if current == "en" else "") + "English",
                f"lang:en:{origin}",
                icons.ENGLISH_FLAG,
                use_icons,
                style="primary" if current == "en" else None,
            ),
        ]
    ]
    if include_back:
        rows.append(
            [
                _button(
                    tr(current, "back_settings"),
                    "menu:settings",
                    icons.BACK,
                    use_icons,
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_keyboard(use_icons: bool, language: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(tr(language, "help"), "menu:help", icons.HELP, use_icons, style="primary"),
                _button(tr(language, "examples"), "menu:examples", icons.ARTICLE, use_icons),
            ],
            [
                _button(
                    tr(language, "settings"),
                    "menu:settings",
                    icons.SETTINGS,
                    use_icons,
                    style="success",
                )
            ],
            [_button(tr(language, "about"), "menu:about", icons.INFO, use_icons)],
        ]
    )


def back_keyboard(
    use_icons: bool, target: str = "main", language: str | None = None
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(
                    tr(language, "back"),
                    f"menu:{target}",
                    icons.BACK,
                    use_icons,
                    style="primary",
                )
            ]
        ]
    )


def settings_keyboard(settings: UserSettings, use_icons: bool) -> InlineKeyboardMarkup:
    language = settings.language
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(
                    tr(language, "appearance"),
                    "settings:appearance",
                    icons.SLIDERS,
                    use_icons,
                ),
                _button(
                    tr(language, "sticker_ids"),
                    "settings:stickers",
                    icons.STICKER,
                    use_icons,
                ),
            ],
            [
                _button(tr(language, "packs"), "settings:packs", icons.FOLDER, use_icons),
                _button(
                    tr(language, "language"),
                    "settings:language",
                    icons.LANGUAGE,
                    use_icons,
                ),
            ],
            [
                _button(
                    tr(language, "reset"),
                    "settings:reset",
                    icons.REFRESH,
                    use_icons,
                    style="danger",
                )
            ],
            [
                _button(
                    tr(language, "main_menu"),
                    "menu:main",
                    icons.BACK,
                    use_icons,
                    style="primary",
                )
            ],
        ]
    )


def appearance_keyboard(settings: UserSettings, use_icons: bool) -> InlineKeyboardMarkup:
    language = settings.language
    custom_label = tr(language, "premium")
    standard_label = tr(language, "standard")
    both_label = tr(language, "both_variants")
    custom = ("✓ " if settings.display_mode == "custom" else "") + custom_label
    standard = ("✓ " if settings.display_mode == "standard" else "") + standard_label
    both = ("✓ " if settings.display_mode == "both" else "") + both_label
    id_labels = {
        "brackets": "[ID]",
        "code": tr(language, "code"),
        "plain": tr(language, "plain"),
    }
    prefix_labels = {
        "number": "1) 2) 3)",
        "bullet": tr(language, "list"),
        "none": tr(language, "no_numbering"),
    }
    separator_labels = {
        "space": tr(language, "space"),
        "dash": tr(language, "dash"),
        "newline": tr(language, "new_line"),
    }

    def toggle_mark(value: bool, label: str) -> str:
        return f"{'✓' if value else '✕'} {label}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(custom, "set:display_mode:custom", icons.PREMIUM, use_icons),
                _button(standard, "set:display_mode:standard", icons.ARTICLE, use_icons),
                _button(both, "set:display_mode:both", icons.MORE, use_icons),
            ],
            [
                _button(
                    ("✓ " if settings.id_style == value else "") + label,
                    f"set:id_style:{value}",
                    icons.CODE,
                    use_icons,
                )
                for value, label in id_labels.items()
            ],
            [
                _button(
                    ("✓ " if settings.prefix_style == value else "") + label,
                    f"set:prefix_style:{value}",
                    icons.LIST,
                    use_icons,
                )
                for value, label in prefix_labels.items()
            ],
            [
                _button(
                    ("✓ " if settings.separator == value else "") + label,
                    f"set:separator:{value}",
                    icons.MORE,
                    use_icons,
                )
                for value, label in separator_labels.items()
            ],
            [
                _button(
                    toggle_mark(
                        settings.space_after_prefix,
                        tr(language, "space_after_prefix"),
                    ),
                    "toggle:space_after_prefix",
                    icons.LIST,
                    use_icons,
                ),
                _button(
                    toggle_mark(
                        settings.spaces_around_dash,
                        tr(language, "spaces_around_dash"),
                    ),
                    "toggle:spaces_around_dash",
                    icons.EDIT,
                    use_icons,
                ),
                _button(
                    toggle_mark(
                        settings.space_between_variants,
                        tr(language, "space_between_variants"),
                    ),
                    "toggle:space_between_variants",
                    icons.PREMIUM,
                    use_icons,
                ),
            ],
            [
                _button(
                    tr(language, "back_settings"),
                    "menu:settings",
                    icons.BACK,
                    use_icons,
                    style="primary",
                )
            ],
        ]
    )


def sticker_settings_keyboard(settings: UserSettings, use_icons: bool) -> InlineKeyboardMarkup:
    language = settings.language
    labels = {
        "file": "file_id",
        "unique": "unique_id",
        "both": tr(language, "both_ids"),
    }
    details_label = tr(language, "technical")
    details = ("✓ " if settings.show_details else "") + details_label
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(
                    ("✓ " if settings.sticker_id_mode == value else "") + label,
                    f"set:sticker_id_mode:{value}",
                    icons.CODE,
                    use_icons,
                )
                for value, label in labels.items()
            ],
            [_button(details, "toggle:show_details", icons.INFO, use_icons)],
            [
                _button(
                    tr(language, "back_settings"),
                    "menu:settings",
                    icons.BACK,
                    use_icons,
                    style="primary",
                )
            ],
        ]
    )


def pack_settings_keyboard(settings: UserSettings, use_icons: bool) -> InlineKeyboardMarkup:
    language = settings.language

    def mark(value: bool, label: str) -> str:
        return f"{'✓ ' if value else ''}{label}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(
                    mark(settings.show_pack_title, tr(language, "pack_title")),
                    "toggle:show_pack_title",
                    icons.ARTICLE,
                    use_icons,
                ),
                _button(
                    mark(settings.show_pack_link, tr(language, "pack_link")),
                    "toggle:show_pack_link",
                    icons.LINK,
                    use_icons,
                ),
            ],
            [
                _button(
                    mark(settings.deduplicate, tr(language, "deduplicate")),
                    "toggle:deduplicate",
                    icons.LIST,
                    use_icons,
                )
            ],
            [
                _button(
                    mark(settings.button_icons, tr(language, "premium_buttons")),
                    "toggle:button_icons",
                    icons.PREMIUM,
                    use_icons,
                )
            ],
            [
                _button(
                    tr(language, "back_settings"),
                    "menu:settings",
                    icons.BACK,
                    use_icons,
                    style="primary",
                )
            ],
        ]
    )


def reset_keyboard(use_icons: bool, language: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(
                    tr(language, "confirm_reset"),
                    "settings:reset_confirm",
                    icons.CONFIRM,
                    use_icons,
                    style="danger",
                ),
                _button(tr(language, "cancel"), "menu:settings", icons.CANCEL, use_icons),
            ]
        ]
    )


def result_keyboard(
    use_icons: bool,
    copy_value: str | None = None,
    export_token: str | None = None,
    language: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if copy_value:
        rows.append(
            [
                _button(
                    tr(language, "copy_id"),
                    None,
                    icons.COPY,
                    use_icons,
                    style="success",
                    copy_text=copy_value,
                )
            ]
        )
    if export_token:
        rows.append(
            [
                _button(
                    tr(language, "export_txt"),
                    f"export:{export_token}",
                    icons.DOWNLOAD,
                    use_icons,
                    style="primary",
                )
            ]
        )
    rows.append(
        [
            _button(tr(language, "settings"), "menu:settings", icons.SETTINGS, use_icons),
            _button(tr(language, "help"), "menu:help", icons.HELP, use_icons),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
