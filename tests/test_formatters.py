from emoji_id_bot.formatters import (
    chunk_line_variants,
    chunk_lines,
    format_emoji_lines,
    is_payment_card_candidate,
    strip_custom_emoji_tags,
)
from emoji_id_bot.models import EmojiItem, UserSettings


def test_custom_and_standard_rendering() -> None:
    item = EmojiItem("custom", "✈️", "6028346797368283073")
    custom = UserSettings(user_id=1, display_mode="custom")
    standard = UserSettings(user_id=1, display_mode="standard")
    assert "<tg-emoji" in format_emoji_lines([item], custom)[0]
    assert "<tg-emoji" not in format_emoji_lines([item], standard)[0]
    assert "[6028346797368283073]" in format_emoji_lines([item], standard)[0]


def test_both_rendering_contains_custom_and_fallback_emoji() -> None:
    item = EmojiItem("custom", "✈️", "6028346797368283073")
    both = UserSettings(user_id=1, display_mode="both")
    rendered = format_emoji_lines([item], both)[0]
    assert "<tg-emoji" in rendered
    assert "</tg-emoji> ✈️" in rendered


def test_prefix_space_can_be_disabled() -> None:
    item = EmojiItem("custom", "✈️", "6028346797368283073")
    settings = UserSettings(user_id=1, space_after_prefix=False)
    assert format_emoji_lines([item], settings)[0].startswith("1)<tg-emoji")


def test_spaces_around_dash_can_be_disabled() -> None:
    item = EmojiItem("custom", "✈️", "6028346797368283073")
    settings = UserSettings(
        user_id=1,
        display_mode="standard",
        separator="dash",
        spaces_around_dash=False,
    )
    assert "✈️—[6028346797368283073]" in format_emoji_lines([item], settings)[0]


def test_space_between_emoji_variants_can_be_disabled() -> None:
    item = EmojiItem("custom", "✈️", "6028346797368283073")
    settings = UserSettings(
        user_id=1,
        display_mode="both",
        space_between_variants=False,
    )
    assert "</tg-emoji>✈️" in format_emoji_lines([item], settings)[0]


def test_chunk_lines_preserves_every_line() -> None:
    lines = ["one", "two", "three"]
    chunks = chunk_lines(lines, limit=7)
    assert chunks == ["one\ntwo", "three"]


def test_strip_custom_emoji_tags_keeps_fallback() -> None:
    text = '<tg-emoji emoji-id="123">✈️</tg-emoji> [123]'
    assert strip_custom_emoji_tags(text) == "✈️ [123]"


def test_chunk_line_variants_keep_matching_boundaries() -> None:
    preferred, fallback = chunk_line_variants(
        ["<tg-emoji>one</tg-emoji>", "two", "three"],
        ["one", "two", "three"],
        limit=30,
    )
    assert preferred == ["<tg-emoji>one</tg-emoji>\ntwo", "three"]
    assert fallback == ["one\ntwo", "three"]


def test_luhn_valid_telegram_id_is_not_rendered_as_a_card_number() -> None:
    identifier = "5456256891548081456"
    assert is_payment_card_candidate(identifier)
    settings = UserSettings(user_id=1, display_mode="standard", id_style="plain")
    rendered = format_emoji_lines(
        [EmojiItem("custom", "🇸🇰", identifier)], settings
    )[0]
    assert "545625689&#8203;1548081456" in rendered


def test_non_card_telegram_id_stays_untouched() -> None:
    identifier = "5456128055414103034"
    assert not is_payment_card_candidate(identifier)
    settings = UserSettings(user_id=1, display_mode="standard", id_style="plain")
    rendered = format_emoji_lines(
        [EmojiItem("custom", "🇸🇰", identifier)], settings
    )[0]
    assert identifier in rendered
    assert "&#8203;" not in rendered
