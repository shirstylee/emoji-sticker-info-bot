from pathlib import Path

import aiosqlite
import pytest

from emoji_id_bot.db import Database


@pytest.mark.asyncio
async def test_settings_are_persisted_and_reset(tmp_path: Path) -> None:
    database = Database(tmp_path / "settings.db")
    await database.connect()
    try:
        defaults = await database.get_settings(42)
        assert defaults.language is None
        assert defaults.display_mode == "custom"
        assert defaults.button_icons is True
        assert defaults.space_after_prefix is True
        assert defaults.spaces_around_dash is True
        assert defaults.space_between_variants is True

        changed_language = await database.set_value(42, "language", "en")
        assert changed_language.language == "en"

        changed = await database.set_value(42, "separator", "dash")
        assert changed.separator == "dash"
        assert (await database.get_settings(42)).separator == "dash"

        spacing = await database.toggle(42, "spaces_around_dash")
        assert spacing.spaces_around_dash is False

        reset = await database.reset(42)
        assert reset.separator == "space"
        assert reset.language == "en"
        assert reset.spaces_around_dash is True
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_existing_database_gets_language_column(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    connection = await aiosqlite.connect(path)
    await connection.execute(
        """
        CREATE TABLE user_settings (
            user_id INTEGER PRIMARY KEY,
            display_mode TEXT NOT NULL DEFAULT 'custom',
            id_style TEXT NOT NULL DEFAULT 'brackets',
            prefix_style TEXT NOT NULL DEFAULT 'number',
            separator TEXT NOT NULL DEFAULT 'space',
            sticker_id_mode TEXT NOT NULL DEFAULT 'file',
            show_pack_title INTEGER NOT NULL DEFAULT 1,
            show_pack_link INTEGER NOT NULL DEFAULT 1,
            show_details INTEGER NOT NULL DEFAULT 0,
            deduplicate INTEGER NOT NULL DEFAULT 0,
            button_icons INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await connection.execute("INSERT INTO user_settings (user_id) VALUES (7)")
    await connection.commit()
    await connection.close()

    database = Database(path)
    await database.connect()
    try:
        settings = await database.get_settings(7)
        assert settings.language is None
        assert settings.space_after_prefix is True
        assert settings.spaces_around_dash is True
        assert settings.space_between_variants is True
        assert (await database.set_value(7, "language", "ru")).language == "ru"
    finally:
        await database.close()
