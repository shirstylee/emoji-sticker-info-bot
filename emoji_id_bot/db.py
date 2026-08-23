from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import aiosqlite

from .models import UserSettings


SETTING_COLUMNS = {
    "language",
    "display_mode",
    "id_style",
    "prefix_style",
    "separator",
    "sticker_id_mode",
    "show_pack_title",
    "show_pack_link",
    "show_details",
    "deduplicate",
    "button_icons",
    "space_after_prefix",
    "spaces_around_dash",
    "space_between_variants",
}


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        await self.connection.execute("PRAGMA journal_mode=WAL")
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT NULL,
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
                space_after_prefix INTEGER NOT NULL DEFAULT 1,
                spaces_around_dash INTEGER NOT NULL DEFAULT 1,
                space_between_variants INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor = await self.connection.execute("PRAGMA table_info(user_settings)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "language" not in columns:
            await self.connection.execute(
                "ALTER TABLE user_settings ADD COLUMN language TEXT DEFAULT NULL"
            )
        boolean_migrations = {
            "space_after_prefix",
            "spaces_around_dash",
            "space_between_variants",
        }
        for column in boolean_migrations - columns:
            await self.connection.execute(
                f"ALTER TABLE user_settings ADD COLUMN {column} "
                "INTEGER NOT NULL DEFAULT 1"
            )
        await self.connection.commit()

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    def _connection(self) -> aiosqlite.Connection:
        if self.connection is None:
            raise RuntimeError("Database is not connected")
        return self.connection

    async def get_settings(self, user_id: int) -> UserSettings:
        connection = self._connection()
        await connection.execute(
            "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,)
        )
        await connection.commit()
        cursor = await connection.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return UserSettings(user_id=user_id)
        return UserSettings(
            user_id=row["user_id"],
            language=row["language"],
            display_mode=row["display_mode"],
            id_style=row["id_style"],
            prefix_style=row["prefix_style"],
            separator=row["separator"],
            sticker_id_mode=row["sticker_id_mode"],
            show_pack_title=bool(row["show_pack_title"]),
            show_pack_link=bool(row["show_pack_link"]),
            show_details=bool(row["show_details"]),
            deduplicate=bool(row["deduplicate"]),
            button_icons=bool(row["button_icons"]),
            space_after_prefix=bool(row["space_after_prefix"]),
            spaces_around_dash=bool(row["spaces_around_dash"]),
            space_between_variants=bool(row["space_between_variants"]),
        )

    async def set_value(self, user_id: int, key: str, value: Any) -> UserSettings:
        if key not in SETTING_COLUMNS:
            raise ValueError(f"Unknown setting: {key}")
        await self.get_settings(user_id)
        connection = self._connection()
        await connection.execute(
            f"UPDATE user_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE user_id = ?",
            (int(value) if isinstance(value, bool) else value, user_id),
        )
        await connection.commit()
        return await self.get_settings(user_id)

    async def toggle(self, user_id: int, key: str) -> UserSettings:
        if key not in SETTING_COLUMNS:
            raise ValueError(f"Unknown setting: {key}")
        settings = await self.get_settings(user_id)
        value = getattr(settings, key)
        if not isinstance(value, bool):
            raise ValueError(f"Setting is not boolean: {key}")
        return await self.set_value(user_id, key, not value)

    async def reset(self, user_id: int) -> UserSettings:
        language = (await self.get_settings(user_id)).language
        connection = self._connection()
        await connection.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        await connection.execute(
            "INSERT INTO user_settings (user_id, language) VALUES (?, ?)",
            (user_id, language),
        )
        await connection.commit()
        return await self.get_settings(user_id)

    async def export_settings(self, user_id: int) -> dict[str, Any]:
        return asdict(await self.get_settings(user_id))
