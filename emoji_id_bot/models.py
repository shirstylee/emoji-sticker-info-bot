from __future__ import annotations

from dataclasses import dataclass


DISPLAY_MODES = ("custom", "standard", "both")
ID_STYLES = ("brackets", "code", "plain")
PREFIX_STYLES = ("number", "bullet", "none")
SEPARATORS = ("space", "dash", "newline")
STICKER_ID_MODES = ("file", "unique", "both")


@dataclass(slots=True)
class UserSettings:
    user_id: int
    display_mode: str = "custom"
    id_style: str = "brackets"
    prefix_style: str = "number"
    separator: str = "space"
    sticker_id_mode: str = "file"
    show_pack_title: bool = True
    show_pack_link: bool = True
    show_details: bool = False
    deduplicate: bool = False
    button_icons: bool = True
    language: str | None = None
    space_after_prefix: bool = True
    spaces_around_dash: bool = True
    space_between_variants: bool = True


@dataclass(frozen=True, slots=True)
class EmojiItem:
    kind: str
    value: str
    identifier: str
    position: int = 0
    set_name: str | None = None


@dataclass(frozen=True, slots=True)
class StickerItem:
    file_id: str
    file_unique_id: str
    emoji: str
    sticker_type: str
    set_name: str | None
    custom_emoji_id: str | None
    is_animated: bool
    is_video: bool
    is_premium: bool
    width: int
    height: int

    @property
    def format_name(self) -> str:
        if self.is_animated:
            return "TGS (анимация)"
        if self.is_video:
            return "WEBM (видео)"
        return "WEBP/PNG (статичный)"


@dataclass(frozen=True, slots=True)
class PackLink:
    kind: str
    name: str
    canonical_url: str
