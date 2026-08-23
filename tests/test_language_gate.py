from emoji_id_bot.handlers import _language_is_selected
from emoji_id_bot.models import UserSettings


def test_language_is_required_until_supported_value_is_saved() -> None:
    assert _language_is_selected(UserSettings(user_id=1)) is False
    assert _language_is_selected(UserSettings(user_id=1, language="")) is False
    assert _language_is_selected(UserSettings(user_id=1, language="de")) is False
    assert _language_is_selected(UserSettings(user_id=1, language="ru")) is True
    assert _language_is_selected(UserSettings(user_id=1, language="en")) is True
