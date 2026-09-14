from emoji_id_bot.keyboards import (
    appearance_keyboard,
    admin_keyboard,
    admins_keyboard,
    admin_confirm_keyboard,
    main_keyboard,
    result_keyboard,
    settings_keyboard,
)
from emoji_id_bot.models import ResultSettings


def test_all_display_modes_share_one_row() -> None:
    keyboard = appearance_keyboard(ResultSettings(), use_icons=True)
    assert [button.callback_data for button in keyboard.inline_keyboard[0]] == [
        "set:display_mode:custom",
        "set:display_mode:standard",
        "set:display_mode:both",
    ]
    assert keyboard.inline_keyboard[0][2].text == "Оба варианта"
    assert keyboard.inline_keyboard[0][2].style is None


def test_regular_main_menu_has_no_settings() -> None:
    labels = [button.text for row in main_keyboard(True).inline_keyboard for button in row]
    assert "Настройки" not in labels
    assert "Настройки результата" not in labels
    assert "Админ-панель" not in labels


def test_result_keyboard_has_txt_export_button() -> None:
    keyboard = result_keyboard(True, copy_value="123", export_token="token")
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    export = next(button for button in buttons if button.text == "Экспорт TXT")
    assert export.callback_data == "export:token"


def test_admin_menu_buttons_have_premium_icons() -> None:
    for keyboard in [admin_keyboard(True), admins_keyboard(frozenset({1}), [2], True),
                     admin_confirm_keyboard(2, "add", True)]:
        assert all(button.icon_custom_emoji_id for row in keyboard.inline_keyboard for button in row)


def test_settings_have_no_language_page() -> None:
    settings = ResultSettings(language="en")
    keyboard = settings_keyboard(settings, True)
    assert not any(
        button.callback_data == "settings:language"
        for row in keyboard.inline_keyboard
        for button in row
    )


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
    assert "Settings" not in labels
    assert "Admin panel" not in labels


def test_appearance_has_all_spacing_toggles_in_one_row() -> None:
    keyboard = appearance_keyboard(ResultSettings(), True)
    callbacks_by_row = [
        [button.callback_data for button in row] for row in keyboard.inline_keyboard
    ]
    assert [
        "toggle:space_after_prefix",
        "toggle:spaces_around_dash",
        "toggle:space_between_variants",
    ] in callbacks_by_row


def test_admin_controls_are_only_shown_to_admins() -> None:
    for builder in (main_keyboard, result_keyboard):
        regular = builder(True)
        admin = builder(True, is_admin=True)
        assert not any(button.callback_data == "admin:main" for row in regular.inline_keyboard for button in row)
        assert any(button.callback_data == "admin:main" for row in admin.inline_keyboard for button in row)


def test_protected_admins_have_no_remove_button() -> None:
    keyboard = admins_keyboard(frozenset({1}), [1, 2], True)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert "admin:remove:1" not in callbacks
    assert "admin:remove:2" in callbacks
