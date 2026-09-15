from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import aiosqlite

from .models import (
    DISPLAY_MODES, ID_STYLES, PREFIX_STYLES, SEPARATORS, STICKER_ID_MODES,
    ResultSettings,
)


CHOICES = {
    "display_mode": DISPLAY_MODES,
    "id_style": ID_STYLES,
    "prefix_style": PREFIX_STYLES,
    "separator": SEPARATORS,
    "sticker_id_mode": STICKER_ID_MODES,
}
DEFAULTS = {
    key: value for key, value in asdict(ResultSettings()).items()
    if key not in {"language", "is_admin", "settings_scope"}
}
BOOLEAN_COLUMNS = {key for key, value in DEFAULTS.items() if isinstance(value, bool)}
SETTING_COLUMNS = set(DEFAULTS)
MAX_ADMINS = 50


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        try:
            connection = self._connection()
            await connection.execute("PRAGMA secure_delete=ON")
            await connection.execute("PRAGMA journal_mode=WAL")
            cursor = await connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_settings'"
            )
            migrating = await cursor.fetchone() is not None
            await cursor.close()
            # Replace legacy individual settings with one shared configuration.
            await connection.execute("DROP TABLE IF EXISTS user_settings")
            await connection.execute(
                "CREATE TABLE IF NOT EXISTS bot_settings ("
                "singleton INTEGER PRIMARY KEY CHECK (singleton = 1), "
                "settings TEXT NOT NULL)"
            )
            await connection.execute(
                "CREATE TABLE IF NOT EXISTS administrators (telegram_id INTEGER PRIMARY KEY)"
            )
            await connection.execute(
                "CREATE TABLE IF NOT EXISTS admin_result_settings ("
                "telegram_id INTEGER PRIMARY KEY, settings TEXT NOT NULL)"
            )
            await connection.execute(
                "INSERT OR IGNORE INTO bot_settings VALUES (1, ?)",
                (json.dumps(DEFAULTS),),
            )
            await connection.commit()
            if migrating:
                await connection.execute("VACUUM")
                cursor = await connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                checkpoint = await cursor.fetchone()
                await cursor.close()
                if checkpoint and checkpoint[0]:
                    raise RuntimeError("Stop other bot processes before migrating the database")
        except BaseException:
            await self.close()
            raise

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    def _connection(self) -> aiosqlite.Connection:
        if self.connection is None:
            raise RuntimeError("Database is not connected")
        return self.connection

    async def get_settings(self, *, admin_id: int | None = None) -> ResultSettings:
        async with self._lock:
            return await self._read(admin_id)

    async def _read(self, admin_id: int | None = None) -> ResultSettings:
        query = ("SELECT settings FROM bot_settings WHERE singleton = 1" if admin_id is None
                 else "SELECT settings FROM admin_result_settings WHERE telegram_id = ?")
        async with self._connection().execute(
            query, () if admin_id is None else (admin_id,)
        ) as cursor:
            row = await cursor.fetchone()
        values = json.loads(row[0]) if row else {}
        for key, value in values.items():
            self._validate(key, value)
        return ResultSettings(**values, settings_scope="global" if admin_id is None else "personal")

    @staticmethod
    def _validate(key: str, value: Any) -> None:
        if key not in SETTING_COLUMNS:
            raise ValueError(f"Unknown setting: {key}")
        if key in BOOLEAN_COLUMNS:
            if type(value) is not bool:
                raise ValueError(f"Setting must be boolean: {key}")
        elif value not in CHOICES[key]:
            raise ValueError(f"Invalid setting value: {key}")

    async def _write(self, settings: ResultSettings, admin_id: int | None = None) -> ResultSettings:
        values = {key: getattr(settings, key) for key in SETTING_COLUMNS}
        if admin_id is None:
            await self._connection().execute(
                "UPDATE bot_settings SET settings = ? WHERE singleton = 1", (json.dumps(values),),
            )
        else:
            await self._connection().execute(
                "INSERT INTO admin_result_settings VALUES (?, ?) "
                "ON CONFLICT(telegram_id) DO UPDATE SET settings=excluded.settings",
                (admin_id, json.dumps(values)),
            )
        settings.settings_scope = "global" if admin_id is None else "personal"
        await self._connection().commit()
        return settings

    async def set_value(self, key: str, value: Any, *, admin_id: int | None = None) -> ResultSettings:
        self._validate(key, value)
        async with self._lock:
            settings = await self._read(admin_id)
            setattr(settings, key, value)
            return await self._write(settings, admin_id)

    async def toggle(self, key: str, *, admin_id: int | None = None) -> ResultSettings:
        if key not in BOOLEAN_COLUMNS:
            raise ValueError(f"Setting is not boolean: {key}")
        async with self._lock:
            settings = await self._read(admin_id)
            setattr(settings, key, not getattr(settings, key))
            return await self._write(settings, admin_id)

    async def reset(self, *, admin_id: int | None = None) -> ResultSettings:
        async with self._lock:
            return await self._write(ResultSettings(), admin_id)

    async def prune_admin_settings(self, root_ids: frozenset[int]) -> None:
        async with self._lock:
            placeholders = ",".join("?" for _ in root_ids)
            await self._connection().execute(
                "DELETE FROM admin_result_settings WHERE telegram_id NOT IN "
                "(SELECT telegram_id FROM administrators) "
                + (f"AND telegram_id NOT IN ({placeholders})" if root_ids else ""),
                tuple(root_ids),
            )
            await self._connection().commit()

    async def is_admin(self, telegram_id: int) -> bool:
        async with self._connection().execute(
            "SELECT 1 FROM administrators WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone() is not None

    async def list_admins(self) -> list[int]:
        async with self._connection().execute(
            "SELECT telegram_id FROM administrators ORDER BY telegram_id"
        ) as cursor:
            return [row[0] for row in await cursor.fetchall()]

    async def add_admin(self, telegram_id: int) -> bool:
        if type(telegram_id) is not int or not 0 < telegram_id < 2**52:
            raise ValueError("Invalid Telegram ID")
        async with self._lock:
            if await self.is_admin(telegram_id):
                return False
            if len(await self.list_admins()) >= MAX_ADMINS:
                raise ValueError("Administrator limit reached")
            await self._connection().execute(
                "INSERT INTO administrators VALUES (?)", (telegram_id,)
            )
            await self._connection().commit()
            return True

    async def remove_admin(self, telegram_id: int) -> None:
        async with self._lock:
            await self._connection().execute(
                "DELETE FROM administrators WHERE telegram_id = ?", (telegram_id,)
            )
            await self._connection().execute(
                "DELETE FROM admin_result_settings WHERE telegram_id = ?", (telegram_id,)
            )
            await self._connection().commit()
