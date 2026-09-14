import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from emoji_id_bot.admin_state import AdminStateStorage


def key(value):
    return StorageKey(bot_id=1, chat_id=value, user_id=value)


@pytest.mark.asyncio
async def test_idle_reads_and_clear_do_not_create_records():
    storage = AdminStateStorage()
    for value in range(1000):
        assert await storage.get_state(key(value)) is None
        assert await storage.get_data(key(value)) == {}
        await FSMContext(storage, key(value)).clear()
    assert not storage._records


@pytest.mark.asyncio
async def test_sessions_are_bounded_expire_and_clear():
    now = [100.0]
    storage = AdminStateStorage(ttl_seconds=60, max_items=2, clock=lambda: now[0])
    await storage.set_state(key(1), "waiting")
    await storage.set_state(key(2), "waiting")
    await storage.set_state(key(3), "waiting")
    assert await storage.get_state(key(1)) is None
    assert await storage.get_state(key(2)) == "waiting"
    now[0] += 60
    assert await storage.get_state(key(2)) is None
    assert not storage._records
    await storage.set_state(key(1), "waiting")
    await FSMContext(storage, key(1)).clear()
    assert not storage._records
