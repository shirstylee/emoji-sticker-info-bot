from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs, urlparse

import emoji as emoji_lib

from .models import EmojiItem, PackLink


WEB_PACK_RE = re.compile(
    r"(?:(?:https?://)?(?:t|telegram)\.me/)(addemoji|addstickers)/([A-Za-z][A-Za-z0-9_]{0,63})",
    re.IGNORECASE,
)
TG_PACK_RE = re.compile(r"tg://(addemoji|addstickers)\?[^\s<>]+", re.IGNORECASE)
CUSTOM_EMOJI_ID_RE = re.compile(r"(?<![A-Za-z0-9_])(\d{15,20})(?![A-Za-z0-9_])")
FILE_ID_RE = re.compile(
    r"(?<![A-Za-z0-9_-])([A-Za-z_-][A-Za-z0-9_-]{19,})(?![A-Za-z0-9_-])"
)
UNICODE_ID_RE = re.compile(
    r"(?<![A-Za-z0-9_])U\+[0-9A-F]{4,6}(?:[ \t]+U\+[0-9A-F]{4,6})*",
    re.IGNORECASE,
)


def extract_pack_links(text: str) -> list[PackLink]:
    found: list[PackLink] = []
    seen: set[tuple[str, str]] = set()

    for match in WEB_PACK_RE.finditer(text):
        action, name = match.groups()
        kind = "emoji" if action.lower() == "addemoji" else "sticker"
        key = (kind, name.lower())
        if key not in seen:
            seen.add(key)
            found.append(
                PackLink(kind=kind, name=name, canonical_url=f"https://t.me/{action.lower()}/{name}")
            )

    for match in TG_PACK_RE.finditer(text):
        parsed = urlparse(match.group(0))
        action = parsed.netloc.lower()
        name = parse_qs(parsed.query).get("set", [""])[0]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
            continue
        kind = "emoji" if action == "addemoji" else "sticker"
        key = (kind, name.lower())
        if key not in seen:
            seen.add(key)
            found.append(
                PackLink(kind=kind, name=name, canonical_url=f"https://t.me/{action}/{name}")
            )
    return found


def extract_telegram_ids(text: str) -> list[str]:
    """Extract custom emoji IDs and reusable Telegram file IDs in source order."""
    text = text.replace("\u200b", "").replace("\u2060", "")
    matches = [
        (match.start(1), match.group(1))
        for pattern in (CUSTOM_EMOJI_ID_RE, FILE_ID_RE)
        for match in pattern.finditer(text)
    ]
    result: list[str] = []
    seen: set[str] = set()
    for _, identifier in sorted(matches):
        if identifier not in seen:
            seen.add(identifier)
            result.append(identifier)
    return result


def extract_unicode_id_items(text: str) -> list[EmojiItem]:
    """Turn identifiers such as U+2708 U+FE0F back into Unicode emoji items."""
    items: list[EmojiItem] = []
    seen: set[str] = set()
    for match in UNICODE_ID_RE.finditer(text):
        code_points = [int(part[2:], 16) for part in match.group(0).split()]
        if any(value > 0x10FFFF or 0xD800 <= value <= 0xDFFF for value in code_points):
            continue
        value = "".join(chr(code_point) for code_point in code_points)
        if not emoji_lib.emoji_list(value):
            continue
        identifier = unicode_identifier(value)
        if identifier in seen:
            continue
        seen.add(identifier)
        items.append(
            EmojiItem(
                kind="unicode",
                value=value,
                identifier=identifier,
                position=match.start(),
            )
        )
    return items


def utf16_span_to_python(text: str, offset: int, length: int) -> tuple[int, int]:
    encoded = text.encode("utf-16-le")
    start_bytes = max(offset, 0) * 2
    end_bytes = max(offset + length, 0) * 2
    start = len(encoded[:start_bytes].decode("utf-16-le", errors="ignore"))
    end = len(encoded[:end_bytes].decode("utf-16-le", errors="ignore"))
    return start, end


def extract_emoji_items(text: str, entities: Iterable[Any] | None) -> list[EmojiItem]:
    items: list[EmojiItem] = []
    custom_spans: list[tuple[int, int]] = []

    for entity in entities or []:
        entity_type = getattr(entity, "type", "")
        type_value = getattr(entity_type, "value", entity_type)
        custom_id = getattr(entity, "custom_emoji_id", None)
        if type_value != "custom_emoji" or not custom_id:
            continue
        start, end = utf16_span_to_python(text, entity.offset, entity.length)
        custom_spans.append((start, end))
        value = text[start:end] or "⭐"
        items.append(
            EmojiItem(kind="custom", value=value, identifier=str(custom_id), position=start)
        )

    for match in emoji_lib.emoji_list(text):
        start = int(match["match_start"])
        end = int(match["match_end"])
        if any(start < span_end and end > span_start for span_start, span_end in custom_spans):
            continue
        value = str(match["emoji"])
        items.append(
            EmojiItem(
                kind="unicode",
                value=value,
                identifier=unicode_identifier(value),
                position=start,
            )
        )

    return sorted(items, key=lambda item: item.position)


def unicode_identifier(value: str) -> str:
    return " ".join(f"U+{ord(character):04X}" for character in value)


def deduplicate_emoji_items(items: list[EmojiItem]) -> list[EmojiItem]:
    result: list[EmojiItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.kind, item.identifier)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
