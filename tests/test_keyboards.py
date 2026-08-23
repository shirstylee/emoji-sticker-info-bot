from emoji_id_bot.keyboards import (
    appearance_keyboard,
    language_keyboard,
    main_keyboard,
    result_keyboard,
    settings_keyboard,
)
from emoji_id_bot.models import UserSettings


def test_all_display_modes_share_one_row() -> None:
    keyboard = appearance_keyboard(UserSettings(user_id=1), use_icons=True)
    assert [button.callback_data for button in keyboard.inline_keyboard[0]] == [
        "set:display_mode:custom",
        "set:display_mode:standard",
        "set:display_mode:both",
    ]
    assert keyboard.inline_keyboard[0][2].text == "Оба варианта"
    assert keyboard.inline_keyboard[0][2].style is None


def test_main_settings_button_has_short_label() -> None:
    labels = [button.text for row in main_keyboard(True).inline_keyboard for button in row]
    assert "Настройки" in labels
    assert "Настройки результата" not in labels


def test_result_keyboard_has_txt_export_button() -> None:
    keyboard = result_keyboard(True, copy_value="123", export_token="token")
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    export = next(button for button in buttons if button.text == "Экспорт TXT")
    assert export.callback_data == "export:token"


def test_language_keyboard_has_onboarding_callbacks() -> None:
    keyboard = language_keyboard(True)
    assert [button.text for button in keyboard.inline_keyboard[0]] == ["Русский", "English"]
    assert [button.callback_data for button in keyboard.inline_keyboard[0]] == [
        "lang:ru:start",
        "lang:en:start",
    ]
    assert [button.icon_custom_emoji_id for button in keyboard.inline_keyboard[0]] == [
        "5449408995691341691",
        "5229192892710402006",
    ]


def test_settings_have_separate_language_page() -> None:
    settings = UserSettings(user_id=1, language="en")
    keyboard = settings_keyboard(settings, True)
    button = next(
        button
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data == "settings:language"
    )
    assert button.text == "Language"


def test_english_result_buttons_are_localized() -> None:
    keyboard = result_keyboard(
        True,
        copy_value="123",
        export_token="token",
        language="en",
    )
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "Copy ID" in labels
    assert "Export TXT" in labels
    assert "Settings" in labels


def test_appearance_has_all_spacing_toggles_in_one_row() -> None:
    keyboard = appearance_keyboard(UserSettings(user_id=1), True)
    callbacks_by_row = [
        [button.callback_data for button in row] for row in keyboard.inline_keyboard
    ]
    assert [
        "toggle:space_after_prefix",
        "toggle:spaces_around_dash",
        "toggle:space_between_variants",
    ] in callbacks_by_row


def test_pack_and_language_buttons_share_one_row() -> None:
    keyboard = settings_keyboard(UserSettings(user_id=1), True)
    callbacks_by_row = [
        [button.callback_data for button in row] for row in keyboard.inline_keyboard
    ]
    assert ["settings:packs", "settings:language"] in callbacks_by_row
