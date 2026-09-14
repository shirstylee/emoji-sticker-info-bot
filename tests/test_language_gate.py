import pytest

from emoji_id_bot.i18n import language_code


@pytest.mark.parametrize("value, expected", [
    (None, "ru"), ("", "ru"), ("de", "ru"), ("ru", "ru"),
    ("en", "en"), ("en-US", "en"), ("EN_gb", "en"),
])
def test_locale_is_resolved_without_onboarding(value, expected):
    assert language_code(value) == expected
