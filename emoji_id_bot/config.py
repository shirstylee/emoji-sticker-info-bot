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

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token.endswith("replace_me"):
            raise RuntimeError(
                "BOT_TOKEN is not configured. Copy .env.example to .env and add the token."
            )

        return cls(
            bot_token=token,
            db_path=Path(os.getenv("DB_PATH", "data/bot.db")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

