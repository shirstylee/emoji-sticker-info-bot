from __future__ import annotations

import html
import json
import re
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass

from .db import SETTING_COLUMNS
from .models import ResultSettings


def settings_json(settings: ResultSettings) -> bytes:
    payload = {
        "schema_version": 1,
        "settings": {key: getattr(settings, key) for key in sorted(SETTING_COLUMNS)},
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


ANCHOR_RE = re.compile(r'<a\s+href="([^"]+)">(.+?)</a>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class StoredExport:
    user_id: int
    filename: str
    content: str
    expires_at: float


class ExportStore:
    def __init__(self, *, ttl_seconds: int = 3600, max_items: int = 500) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: OrderedDict[str, StoredExport] = OrderedDict()

    def put(self, user_id: int, filename: str, content: str) -> str:
        self._purge()
        while len(self._items) >= self.max_items:
            self._items.popitem(last=False)
        token = secrets.token_urlsafe(8)
        while token in self._items:
            token = secrets.token_urlsafe(8)
        self._items[token] = StoredExport(
            user_id=user_id,
            filename=filename,
            content=content,
            expires_at=time.monotonic() + self.ttl_seconds,
        )
        return token

    def get(self, token: str, user_id: int) -> StoredExport | None:
        self._purge()
        item = self._items.get(token)
        if item is None or item.user_id != user_id:
            return None
        self._items.move_to_end(token)
        return item

    @property
    def active_count(self) -> int:
        self._purge()
        return len(self._items)

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [token for token, item in self._items.items() if item.expires_at <= now]
        for token in expired:
            self._items.pop(token, None)


def html_lines_to_text(lines: list[str]) -> str:
    text = "\n".join(lines)

    def replace_anchor(match: re.Match[str]) -> str:
        url = html.unescape(match.group(1))
        label = TAG_RE.sub("", match.group(2))
        return f"{label}: {url}"

    text = ANCHOR_RE.sub(replace_anchor, text)
    text = TAG_RE.sub("", text)
    text = html.unescape(text).replace("\u200b", "").replace("\u2060", "")
    return text.strip() + "\n"


def safe_export_filename(prefix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", prefix).strip("_")
    return f"{normalized[:60] or 'result'}.txt"
