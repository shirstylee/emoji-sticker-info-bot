from types import SimpleNamespace

import pytest

from emoji_id_bot.extractors import (
    extract_emoji_items,
    extract_pack_links,
    extract_telegram_ids,
    extract_unicode_id_items,
    unicode_identifier,
    utf16_span_to_python,
)
from emoji_id_bot.handlers import _enrich_custom_emoji
from emoji_id_bot.models import EmojiItem


def test_extracts_web_and_tg_pack_links_without_duplicates() -> None:
    links = extract_pack_links(
        "https://t.me/addemoji/MyPack tg://addstickers?set=Sticker_pack "
        "https://telegram.me/addemoji/MyPack"
    )
    assert [(link.kind, link.name) for link in links] == [
        ("emoji", "MyPack"),
        ("sticker", "Sticker_pack"),
    ]


def test_utf16_offset_after_astral_character() -> None:
    text = "😀 x ✈️"
    # Telegram offsets count 😀 as two UTF-16 code units.
    start, end = utf16_span_to_python(text, 5, 2)
    assert text[start:end] == "✈️"


def test_custom_entity_is_not_duplicated_as_unicode() -> None:
    text = "✈️ 🍏"
    entity = SimpleNamespace(
        type="custom_emoji",
        offset=0,
        length=2,
        custom_emoji_id="6028346797368283073",
    )
    items = extract_emoji_items(text, [entity])
    assert [(item.kind, item.value) for item in items] == [
        ("custom", "✈️"),
        ("unicode", "🍏"),
    ]


def test_unicode_identifier_keeps_variation_selector() -> None:
    assert unicode_identifier("✈️") == "U+2708 U+FE0F"


def test_extracts_custom_emoji_and_file_ids_without_duplicates() -> None:
    file_id = "CAACAgIAAxkBAAIBQ2example_file_id_123456789"
    assert extract_telegram_ids(
        f"[602834679\u200b7368283073]\nfile_id: {file_id}\n6028346797368283073"
    ) == ["6028346797368283073", file_id]


def test_turns_unicode_identifiers_back_into_emoji() -> None:
    items = extract_unicode_id_items("U+1F34F\nU+2708 U+FE0F")
    assert [(item.value, item.identifier) for item in items] == [
        ("🍏", "U+1F34F"),
        ("✈️", "U+2708 U+FE0F"),
    ]


def test_rejects_non_emoji_unicode_identifiers() -> None:
    assert extract_unicode_id_items("U+0041") == []


@pytest.mark.asyncio
async def test_custom_emoji_enrichment_uses_api_batches_of_200() -> None:
    class FakeBot:
        def __init__(self) -> None:
            self.batch_sizes: list[int] = []

        async def get_custom_emoji_stickers(self, custom_emoji_ids: list[str]):
            self.batch_sizes.append(len(custom_emoji_ids))
            return []

    bot = FakeBot()
    items = [EmojiItem("custom", "⭐", str(index), index) for index in range(201)]
    assert await _enrich_custom_emoji(bot, items) == items
    assert bot.batch_sizes == [200, 1]
