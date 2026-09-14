from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Chat, Message, User, Sticker

from emoji_id_bot.db import Database
from emoji_id_bot.exports import ExportStore
from emoji_id_bot.handlers import (
    AdminInput, _disable_icons, _get_settings, callbacks, command_admin,
    command_start, handle_sticker, handle_text, receive_admin_id,
)
from emoji_id_bot.models import ResultSettings
from emoji_id_bot.security import RequestProtection
from emoji_id_bot.admin_state import AdminStateStorage


ROOTS = frozenset({100})


def message(user_id=100, text="/admin", language="ru", **kwargs):
    return Message(message_id=1, date=datetime.now(timezone.utc),
                   chat=Chat(id=user_id, type="private"),
                   from_user=User(id=user_id, is_bot=False, first_name="Test", language_code=language),
                   text=text, **kwargs)


def callback(data, user_id=100, language="ru"):
    event = message(user_id, language=language)
    return CallbackQuery(id="test", from_user=event.from_user, chat_instance="test",
                         message=event, data=data)


@pytest_asyncio.fixture
async def database(tmp_path):
    db = Database(tmp_path / "test.db")
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def state():
    return FSMContext(storage=AdminStateStorage(), key=StorageKey(bot_id=1, chat_id=100, user_id=100))


@pytest.fixture
def responses(monkeypatch):
    answer, edit, alert, document = (AsyncMock() for _ in range(4))
    monkeypatch.setattr(Message, "answer", answer)
    monkeypatch.setattr(Message, "edit_text", edit)
    monkeypatch.setattr(Message, "answer_document", document)
    monkeypatch.setattr(CallbackQuery, "answer", alert)
    return answer, edit, alert, document


@pytest.mark.asyncio
@pytest.mark.parametrize("data", [
    "menu:settings", "settings:appearance", "settings:stickers", "settings:packs",
    "settings:language", "settings:reset", "settings:reset_confirm", "set:display_mode:custom",
    "toggle:show_details", "lang:en:start", "admin:main", "admin:list", "admin:add",
    "admin:confirm_add:300", "admin:remove:100", "admin:confirm_remove:100",
])
async def test_regular_user_cannot_use_old_or_forged_admin_buttons(database, state, responses, data):
    await callbacks(callback(data, 200), database, ExportStore(), state, ROOTS)
    answer, edit, alert, _ = responses
    edit.assert_not_awaited()
    answer.assert_not_awaited()
    assert alert.await_args.kwargs["show_alert"] is True
    assert "администраторам" in alert.await_args.args[0]
    assert await database.get_settings() == ResultSettings()
    assert await database.list_admins() == []


@pytest.mark.asyncio
async def test_admin_command_checks_permissions(database, state, responses):
    answer = responses[0]
    await command_admin(message(200), database, state, ROOTS)
    assert "администраторам" in answer.await_args.args[0]
    await command_admin(message(), database, state, ROOTS)
    assert "Админ-панель" in answer.await_args.args[0]
    assert "<blockquote>" in answer.await_args.args[0]
    assert all(button.icon_custom_emoji_id for row in answer.await_args.kwargs["reply_markup"].inline_keyboard for button in row)


@pytest.mark.asyncio
async def test_regular_start_is_immediate_and_locale_is_contextual(database, state, responses):
    await command_start(message(200, "/start", "en-US"), database, state, ROOTS)
    answer = responses[0]
    assert "Send me" in answer.await_args.args[0]
    assert "Choose your language" not in answer.await_args.args[0]
    buttons = [button.callback_data for row in answer.await_args.kwargs["reply_markup"].inline_keyboard for button in row]
    assert "menu:settings" not in buttons
    assert "admin:main" not in buttons
    assert (await _get_settings(database, message(201, language="ru").from_user, ROOTS)).language == "ru"
    assert (await database.get_settings()).language is None


@pytest.mark.asyncio
async def test_admin_changes_are_shared_and_keep_locale(database, state, responses):
    await callbacks(callback("set:display_mode:both", language="en"), database, ExportStore(), state, ROOTS)
    assert "Result appearance" in responses[1].await_args.args[0]
    settings = await _get_settings(database, message(200).from_user, ROOTS)
    assert settings.display_mode == "both"
    assert settings.is_admin is False
    assert settings.language == "ru"


@pytest.mark.asyncio
async def test_add_admin_requires_confirmation_and_grants_access(database, state, responses):
    exports = ExportStore()
    await callbacks(callback("admin:add"), database, exports, state, ROOTS)
    assert await state.get_state() == AdminInput.telegram_id.state
    await receive_admin_id(message(text="200"), database, state, ROOTS)
    assert "Выдать права" in responses[0].await_args.args[0]
    assert not await database.is_admin(200)
    await callbacks(callback("admin:confirm_add:200"), database, exports, state, ROOTS)
    assert await database.is_admin(200)
    await command_admin(message(200), database, state, ROOTS)
    assert "Админ-панель" in responses[0].await_args.args[0]
    await callbacks(callback("admin:confirm_add:300", 200), database, exports, state, ROOTS)
    assert await database.is_admin(300)


@pytest.mark.asyncio
async def test_revoked_admin_cannot_use_stale_buttons_or_pending_input(database, state, responses):
    await database.add_admin(200)
    await state.set_state(AdminInput.telegram_id)
    await callbacks(callback("admin:remove:200"), database, ExportStore(), state, ROOTS)
    assert await database.is_admin(200)
    await callbacks(callback("admin:confirm_remove:200"), database, ExportStore(), state, ROOTS)
    assert not await database.is_admin(200)
    await state.set_state(AdminInput.telegram_id)
    await receive_admin_id(message(200, "300"), database, state, ROOTS)
    assert await state.get_state() is None
    assert not await database.is_admin(300)
    await callbacks(callback("set:display_mode:both", 200), database, ExportStore(), state, ROOTS)
    assert (await database.get_settings()).display_mode == "standard"


@pytest.mark.asyncio
async def test_env_admin_cannot_be_removed_and_reset_keeps_admins(database, state, responses):
    await database.add_admin(200)
    await callbacks(callback("admin:confirm_remove:100", 200), database, ExportStore(), state, ROOTS)
    assert ".env" in responses[2].await_args.args[0]
    assert (await _get_settings(database, message().from_user, ROOTS)).is_admin
    await callbacks(callback("settings:reset_confirm", 200), database, ExportStore(), state, ROOTS)
    assert await database.is_admin(200)


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["@user", "-123", "0", "123,456", "１２３", "9999999999999999999"])
async def test_admin_input_rejects_invalid_ids(database, state, responses, value):
    await state.set_state(AdminInput.telegram_id)
    await receive_admin_id(message(text=value), database, state, ROOTS)
    assert await state.get_state() == AdminInput.telegram_id.state
    assert await database.list_admins() == []


@pytest.mark.asyncio
async def test_icon_fallback_is_local(database):
    settings = await database.get_settings()
    await _disable_icons(database, settings)
    assert not settings.button_icons
    assert (await database.get_settings()).button_icons


@pytest.mark.asyncio
async def test_default_output_and_txt_match_sample(database, responses):
    exports = ExportStore()
    await handle_text(message(200, "🏐"), AsyncMock(), database, exports, RequestProtection(), ROOTS)
    answer = responses[0]
    assert answer.await_args.args[0] == "🏐 - U+1F3D0"
    buttons = [button for row in answer.await_args.kwargs["reply_markup"].inline_keyboard for button in row]
    assert not any(button.callback_data in {"menu:settings", "admin:main"} for button in buttons)
    token = next(button.callback_data.split(":")[1] for button in buttons if (button.callback_data or "").startswith("export:"))
    assert exports.get(token, 200).content == "🏐 - U+1F3D0\n"
    assert exports.get(token, 201) is None


@pytest.mark.asyncio
async def test_default_sticker_output(database, responses):
    sticker = Sticker(file_id="file_test", file_unique_id="unique_test", type="regular",
                      width=512, height=512, is_animated=False, is_video=False, emoji="🏐")
    await handle_sticker(message(200, text=None, sticker=sticker), database, ExportStore(), ROOTS)
    assert responses[0].await_args.args[0] == "🏐 - file_test"


@pytest.mark.asyncio
@pytest.mark.parametrize("data", ["set:", "toggle:unknown", "admin:confirm_add:abc", "admin:confirm_add:extra:200", "settings:language", "lang:en:start"])
async def test_stale_or_malformed_admin_callback_is_safe(database, state, responses, data):
    await callbacks(callback(data), database, ExportStore(), state, ROOTS)
    assert await database.get_settings() == ResultSettings()
    assert await database.list_admins() == []


@pytest.mark.asyncio
async def test_dispatcher_routes_admin_flow_and_regular_result(database, responses):
    from aiogram import Bot, Dispatcher
    from aiogram.types import Update
    from emoji_id_bot.handlers import router

    bot = Bot(token="123456:" + "x" * 35)
    dispatcher = Dispatcher(storage=AdminStateStorage())
    dispatcher.include_router(router)
    context = dict(db=database, exports=ExportStore(), protection=RequestProtection(), admin_ids=ROOTS)
    try:
        await dispatcher.feed_update(bot, Update(update_id=1, message=message()), **context)
        assert "Админ-панель" in responses[0].await_args.args[0]
        await dispatcher.feed_update(bot, Update(update_id=2, callback_query=callback("admin:add")), **context)
        await dispatcher.feed_update(bot, Update(update_id=3, message=message(text="200")), **context)
        assert "Выдать права" in responses[0].await_args.args[0]
        assert not await database.is_admin(200)
        await dispatcher.feed_update(bot, Update(update_id=4, callback_query=callback("admin:confirm_add:200")), **context)
        assert await database.is_admin(200)
        await dispatcher.feed_update(bot, Update(update_id=5, message=message(300, "🏐")), **context)
        assert responses[0].await_args.args[0] == "🏐 - U+1F3D0"
        assert not dispatcher.storage._records
    finally:
        await dispatcher.storage.close()
        await bot.session.close()
