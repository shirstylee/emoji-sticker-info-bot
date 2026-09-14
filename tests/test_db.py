import asyncio
import json
from pathlib import Path

import aiosqlite
import pytest

from emoji_id_bot.db import Database, MAX_ADMINS
from emoji_id_bot.models import ResultSettings


@pytest.mark.asyncio
async def test_shared_settings_persist_and_reset(tmp_path: Path) -> None:
    database = Database(tmp_path / "settings.db")
    await database.connect()
    try:
        assert await database.get_settings() == ResultSettings()
        await database.set_value("display_mode", "both")
        await database.toggle("spaces_around_dash")
        await database.add_admin(42)
        await database.close()
        await database.connect()
        assert (await database.get_settings()).display_mode == "both"
        assert (await database.get_settings()).spaces_around_dash is False
        assert await database.reset() == ResultSettings()
        assert await database.is_admin(42)
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_legacy_database_migration(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    async with aiosqlite.connect(path) as connection:
        await connection.execute("CREATE TABLE user_settings (user_id INTEGER PRIMARY KEY, language TEXT)")
        await connection.execute("INSERT INTO user_settings VALUES (123, 'legacy_test_marker')")
        await connection.commit()
    database = Database(path)
    await database.connect()
    try:
        assert await database.get_settings() == ResultSettings()
        cursor = await database.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        assert {row[0] for row in await cursor.fetchall()} == {"bot_settings", "administrators"}
        assert await database.list_admins() == []
        cursor = await database.connection.execute("SELECT settings FROM bot_settings")
        values = json.loads((await cursor.fetchone())[0])
        assert not {"user_id", "language", "is_admin"} & values.keys()
    finally:
        await database.close()
    assert b"legacy_test_marker" not in path.read_bytes()


@pytest.mark.asyncio
async def test_concurrent_settings_updates_do_not_overwrite_each_other(tmp_path: Path) -> None:
    database = Database(tmp_path / "settings.db")
    await database.connect()
    try:
        await asyncio.gather(database.set_value("display_mode", "both"),
                             database.set_value("id_style", "code"))
        settings = await database.get_settings()
        assert settings.display_mode == "both"
        assert settings.id_style == "code"
        await asyncio.gather(*(database.toggle("show_details") for _ in range(10)))
        assert (await database.get_settings()).show_details is False
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_settings_validate_names_and_values(tmp_path: Path) -> None:
    database = Database(tmp_path / "settings.db")
    await database.connect()
    try:
        for key, value in [("language", "en"), ("user_id", 123), ("display_mode", "invalid"),
                           ("show_details", "false"), ("is_admin", True)]:
            with pytest.raises(ValueError):
                await database.set_value(key, value)
        with pytest.raises(ValueError):
            await database.toggle("display_mode")
        assert await database.get_settings() == ResultSettings()
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_administrator_storage_is_bounded_and_persistent(tmp_path: Path) -> None:
    database = Database(tmp_path / "settings.db")
    await database.connect()
    try:
        assert await database.add_admin(1)
        assert not await database.add_admin(1)
        for value in range(2, MAX_ADMINS + 1):
            await database.add_admin(value)
        with pytest.raises(ValueError):
            await database.add_admin(MAX_ADMINS + 1)
        await database.remove_admin(1)
        assert not await database.is_admin(1)
        await database.close()
        await database.connect()
        assert len(await database.list_admins()) == MAX_ADMINS - 1
    finally:
        await database.close()
