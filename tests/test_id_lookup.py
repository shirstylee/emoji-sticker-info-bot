from types import SimpleNamespace

import pytest

from emoji_id_bot.exports import ExportStore
from emoji_id_bot.handlers import _handle_id_lookup
from emoji_id_bot.models import UserSettings


class FakeMessage:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.answers: list[str] = []
        self.stickers: list[str] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append(text)

    async def answer_sticker(self, sticker: str, **kwargs: object) -> None:
        self.stickers.append(sticker)


class FakeBot:
    async def get_custom_emoji_stickers(self, custom_emoji_ids: list[str]):
        return [
            SimpleNamespace(
                custom_emoji_id=identifier,
                emoji="✈️",
                set_name="TestEmojiPack",
            )
            for identifier in custom_emoji_ids
        ]


@pytest.mark.asyncio
async def test_custom_and_unicode_ids_are_displayed() -> None:
    message = FakeMessage()
    handled = await _handle_id_lookup(
        message,
        FakeBot(),
        object(),
        ExportStore(),
        UserSettings(user_id=42, language="ru", button_icons=False),
        "6028346797368283073\nU+1F34F",
    )
    assert handled is True
    assert any("6028346797368283073" in answer for answer in message.answers)
    assert any("🍏" in answer for answer in message.answers)
    assert any("<tg-emoji" in answer for answer in message.answers)


@pytest.mark.asyncio
async def test_sticker_file_id_sends_the_sticker() -> None:
    file_id = "CAACAgIAAxkBAAIBQ2example_file_id_123456789"
    message = FakeMessage()
    handled = await _handle_id_lookup(
        message,
        FakeBot(),
        object(),
        ExportStore(),
        UserSettings(user_id=42, language="en", button_icons=False),
        file_id,
    )
    assert handled is True
    assert message.stickers == [file_id]
