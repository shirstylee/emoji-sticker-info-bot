from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    db_path: Path
    log_level: str
    admin_ids: frozenset[int]

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token.endswith("replace_me"):
            raise RuntimeError(
                "BOT_TOKEN is not configured. Copy .env.example to .env and add the token."
            )

        raw_admin_ids = os.getenv("ADMIN_IDS", "").strip()
        parts = [part.strip() for part in raw_admin_ids.split(",")]
        if len(parts) > 50 or not all(
            part.isascii() and part.isdigit() and len(part) <= 16 and 0 < int(part) < 2**52
            for part in parts
        ):
            raise RuntimeError(
                "ADMIN_IDS is required: set positive numeric Telegram user IDs "
                "separated by commas in .env."
            )

        return cls(
            bot_token=token,
            db_path=Path(os.getenv("DB_PATH", "data/bot.db")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            admin_ids=frozenset(int(part) for part in parts),
        )
