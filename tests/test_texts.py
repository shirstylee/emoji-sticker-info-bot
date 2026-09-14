from emoji_id_bot.models import ResultSettings
from emoji_id_bot.texts import (
    ABOUT_TEXT,
    EXAMPLES_TEXT,
    HELP_TEXT,
    MAIN_TEXT,
    PACK_SETTINGS_TEXT,
    RESET_TEXT,
    STICKER_SETTINGS_TEXT,
    admin_text,
    admins_text,
    admin_prompt_text,
    admin_confirm_text,
    appearance_text,
    help_text,
    main_text,
    settings_text,
)


def test_all_menu_pages_use_custom_emoji_icons() -> None:
    settings = ResultSettings()
    pages = [
        MAIN_TEXT,
        HELP_TEXT,
        EXAMPLES_TEXT,
        ABOUT_TEXT,
        settings_text(settings),
        appearance_text(settings),
        STICKER_SETTINGS_TEXT,
        PACK_SETTINGS_TEXT,
        RESET_TEXT,
    ]
    assert all("<tg-emoji" in page for page in pages)


def test_main_menu_uses_bulleted_input_list() -> None:
    assert MAIN_TEXT.count("\n• ") == 5


def test_settings_describe_both_display_mode() -> None:
    settings = ResultSettings(display_mode="both")
    assert "Premium + обычный emoji" in settings_text(settings)
    assert "<tg-emoji" in appearance_text(settings)
    assert "</tg-emoji> ✈️" in appearance_text(settings)


def test_code_and_plain_previews_are_visually_distinct() -> None:
    code = appearance_text(ResultSettings(id_style="code"))
    plain = appearance_text(ResultSettings(id_style="plain"))
    assert "<code>6028346797368283073</code>" in code
    assert "<code>6028346797368283073</code>" not in plain


def test_sticker_settings_explain_every_id_mode() -> None:
    assert "<b>file_id</b>" in STICKER_SETTINGS_TEXT
    assert "<b>unique_id</b>" in STICKER_SETTINGS_TEXT
    assert "<b>Оба ID</b>" in STICKER_SETTINGS_TEXT
    assert "отправить или скачать" in STICKER_SETTINGS_TEXT


def test_admin_pages_use_quotes_and_premium_emoji() -> None:
    for language in ("ru", "en"):
        settings = ResultSettings(language=language)
        pages = [admin_text(language), admins_text(frozenset({1}), [2], language),
                 admin_prompt_text(language), admin_confirm_text(2, "add", language),
                 settings_text(settings), appearance_text(settings)]
        for page in pages:
            assert "<blockquote>" in page
            assert "<tg-emoji" in page
            assert len(page) < 3900


def test_largest_admin_list_fits_a_telegram_message() -> None:
    roots = frozenset(range(4503599627370300, 4503599627370350))
    extra = list(range(4503599627370400, 4503599627370450))
    for language in ("ru", "en"):
        assert len(admins_text(roots, extra, language)) < 4096


def test_english_pages_are_localized() -> None:
    settings = ResultSettings(language="en")
    assert "Send me" in main_text("en")
    assert "How to use" in help_text("en")
    assert "Result settings" in settings_text(settings)


def test_appearance_preview_uses_current_spacing_choices() -> None:
    settings = ResultSettings(
        prefix_style="number",
        id_style="brackets",
        display_mode="both",
        separator="dash",
        space_after_prefix=False,
        spaces_around_dash=False,
        space_between_variants=False,
    )
    text = appearance_text(settings)
    assert "1)<tg-emoji" in text
    assert "</tg-emoji>✈️-[6028346797368283073]" in text


def test_boolean_settings_use_checkmarks_and_crosses() -> None:
    text = settings_text(
        ResultSettings(show_details=False, show_pack_title=True)
    )
    assert "✅" in text
    assert "❌" in text
    assert ">да</b>" not in text
    assert ">нет</b>" not in text
