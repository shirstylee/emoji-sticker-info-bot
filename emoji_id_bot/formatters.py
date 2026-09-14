from __future__ import annotations

import html
import re
from collections.abc import Iterable

from . import icons
from .i18n import language_code, tr
from .models import EmojiItem, StickerItem, ResultSettings


MAX_MESSAGE_LENGTH = 3900


def _prefix(index: int, settings: ResultSettings) -> str:
    if settings.prefix_style == "number":
        return f"{index})"
    if settings.prefix_style == "bullet":
        return "•"
    return ""


def _separator(settings: ResultSettings) -> str:
    if settings.separator == "dash":
        return " - " if settings.spaces_around_dash else "-"
    if settings.separator == "newline":
        return "\n"
    return " "


def is_payment_card_candidate(identifier: str) -> bool:
    """Match numeric IDs Telegram may auto-detect as bank card numbers."""
    if not identifier.isascii() or not identifier.isdigit() or not 13 <= len(identifier) <= 19:
        return False
    total = 0
    parity = len(identifier) % 2
    for index, character in enumerate(identifier):
        digit = int(character)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _safe_plain_identifier(identifier: str) -> str:
    escaped = html.escape(identifier)
    if not is_payment_card_candidate(identifier):
        return escaped
    midpoint = len(identifier) // 2
    # Telegram otherwise offers "Copy card" for coincidental Luhn-valid IDs.
    # The zero-width space is removed again when generating TXT exports.
    return f"{escaped[:midpoint]}&#8203;{escaped[midpoint:]}"


def _id(identifier: str, settings: ResultSettings) -> str:
    if settings.id_style == "code":
        return f"<code>{html.escape(identifier)}</code>"
    escaped = _safe_plain_identifier(identifier)
    if settings.id_style == "plain":
        return escaped
    return f"[{escaped}]"


def _visual(value: str, custom_id: str | None, settings: ResultSettings) -> str:
    escaped = html.escape(value or "⭐")
    if custom_id and settings.display_mode in {"custom", "both"}:
        custom = f'<tg-emoji emoji-id="{html.escape(custom_id)}">{escaped}</tg-emoji>'
        if settings.display_mode == "both":
            gap = " " if settings.space_between_variants else ""
            return f"{custom}{gap}{escaped}"
        return custom
    return escaped


def _prefix_and_visual(prefix: str, visual: str, settings: ResultSettings) -> str:
    if not prefix:
        return visual
    gap = " " if settings.space_after_prefix else ""
    return f"{prefix}{gap}{visual}"


def format_emoji_lines(items: Iterable[EmojiItem], settings: ResultSettings) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        prefix = _prefix(index, settings)
        visual = _visual(item.value, item.identifier if item.kind == "custom" else None, settings)
        identifier = _id(item.identifier, settings)
        left = _prefix_and_visual(prefix, visual, settings)
        lines.append(f"{left}{_separator(settings)}{identifier}".strip())
        if settings.show_details and item.set_name:
            lines.append(
                f"   {tr(settings.language, 'pack')}: <code>{html.escape(item.set_name)}</code>"
            )
    return lines


def sticker_from_telegram(sticker: object) -> StickerItem:
    return StickerItem(
        file_id=str(getattr(sticker, "file_id")),
        file_unique_id=str(getattr(sticker, "file_unique_id")),
        emoji=str(getattr(sticker, "emoji", None) or "🖼"),
        sticker_type=str(getattr(sticker, "type", "regular")),
        set_name=getattr(sticker, "set_name", None),
        custom_emoji_id=getattr(sticker, "custom_emoji_id", None),
        is_animated=bool(getattr(sticker, "is_animated", False)),
        is_video=bool(getattr(sticker, "is_video", False)),
        is_premium=getattr(sticker, "premium_animation", None) is not None,
        width=int(getattr(sticker, "width", 0)),
        height=int(getattr(sticker, "height", 0)),
    )


def format_sticker_lines(
    stickers: Iterable[StickerItem], settings: ResultSettings, *, compact: bool
) -> list[str]:
    lines: list[str] = []
    for index, sticker in enumerate(stickers, start=1):
        prefix = _prefix(index, settings)
        visual = _visual(sticker.emoji, sticker.custom_emoji_id, settings)
        left = _prefix_and_visual(prefix, visual, settings)

        if sticker.custom_emoji_id:
            primary = _id(sticker.custom_emoji_id, settings)
        elif settings.sticker_id_mode == "unique":
            primary = _id(sticker.file_unique_id, settings)
        else:
            primary = _id(sticker.file_id, settings)
        lines.append(f"{left}{_separator(settings)}{primary}".strip())

        if settings.sticker_id_mode == "both":
            if sticker.custom_emoji_id:
                lines.append(f"   file_id: <code>{html.escape(sticker.file_id)}</code>")
                lines.append(f"   unique_id: <code>{html.escape(sticker.file_unique_id)}</code>")
            else:
                lines.append(f"   unique_id: <code>{html.escape(sticker.file_unique_id)}</code>")
        elif settings.sticker_id_mode == "file" and sticker.custom_emoji_id and not compact and settings.show_details:
            lines.append(f"   file_id: <code>{html.escape(sticker.file_id)}</code>")
        elif settings.sticker_id_mode == "unique" and sticker.custom_emoji_id and not compact and settings.show_details:
            lines.append(f"   unique_id: <code>{html.escape(sticker.file_unique_id)}</code>")

        if settings.show_details:
            premium = tr(settings.language, "yes") if sticker.is_premium else tr(
                settings.language, "no"
            )
            if language_code(settings.language) == "en":
                format_name = (
                    "TGS (animated)"
                    if sticker.is_animated
                    else "WEBM (video)"
                    if sticker.is_video
                    else "WEBP/PNG (static)"
                )
            else:
                format_name = sticker.format_name
            lines.append(
                "   "
                f"{tr(settings.language, 'type')}: {html.escape(sticker.sticker_type)} · "
                f"{format_name} · "
                f"{sticker.width}×{sticker.height} · Premium: {premium}"
            )
            if sticker.set_name and not compact:
                lines.append(
                    f"   {tr(settings.language, 'pack')}: "
                    f"<code>{html.escape(sticker.set_name)}</code>"
                )
    return lines


def pack_header(
    title: str,
    count: int,
    sticker_type: str,
    url: str,
    settings: ResultSettings,
) -> list[str]:
    lines: list[str] = []
    if settings.show_pack_title:
        kind = tr(
            settings.language,
            "emoji_count" if sticker_type == "custom_emoji" else "sticker_count",
        )
        lines.append(
            f"{icons.tag(icons.FILE, '📁')} <b>{html.escape(title)}</b> — {count} {kind}"
        )
    if settings.show_pack_link:
        lines.append(
            f'{icons.tag(icons.LINK, "🔗")} '
            f'<a href="{html.escape(url, quote=True)}">'
            f'{tr(settings.language, "open_pack")}</a>'
        )
    if lines:
        lines.append("")
    return lines


def chunk_lines(lines: Iterable[str], limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for line in lines:
        addition = len(line) + (1 if current else 0)
        if current and current_length + addition > limit:
            chunks.append("\n".join(current))
            current = [line]
            current_length = len(line)
        else:
            current.append(line)
            current_length += addition
    if current:
        chunks.append("\n".join(current))
    return chunks or [""]


def chunk_line_variants(
    preferred_lines: list[str], fallback_lines: list[str], limit: int = MAX_MESSAGE_LENGTH
) -> tuple[list[str], list[str]]:
    """Split two line-for-line variants at identical item boundaries."""
    if len(preferred_lines) != len(fallback_lines):
        raise ValueError("Preferred and fallback variants must have the same line count")

    preferred_chunks: list[str] = []
    fallback_chunks: list[str] = []
    current_preferred: list[str] = []
    current_fallback: list[str] = []
    current_length = 0

    for preferred, fallback in zip(preferred_lines, fallback_lines, strict=True):
        addition = len(preferred) + (1 if current_preferred else 0)
        if current_preferred and current_length + addition > limit:
            preferred_chunks.append("\n".join(current_preferred))
            fallback_chunks.append("\n".join(current_fallback))
            current_preferred = [preferred]
            current_fallback = [fallback]
            current_length = len(preferred)
        else:
            current_preferred.append(preferred)
            current_fallback.append(fallback)
            current_length += addition

    if current_preferred:
        preferred_chunks.append("\n".join(current_preferred))
        fallback_chunks.append("\n".join(current_fallback))
    return preferred_chunks or [""], fallback_chunks or [""]


CUSTOM_EMOJI_OPEN_TAG_RE = re.compile(r'<tg-emoji\s+emoji-id="[^"]+">')


def strip_custom_emoji_tags(text: str) -> str:
    """Keep the fallback emoji while removing Telegram custom-emoji entities."""
    return CUSTOM_EMOJI_OPEN_TAG_RE.sub("", text).replace("</tg-emoji>", "")
