from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import OrderedDict, deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message, TelegramObject

from .i18n import language_code, tr


logger = logging.getLogger(__name__)


class SlidingWindowLimiter:
    """Small in-memory limiter that does not require Redis or another service."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: float,
        max_keys: int = 100_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit < 1 or window_seconds <= 0 or max_keys < 1:
            raise ValueError("Rate-limit values must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._clock = clock
        self._events: OrderedDict[int, deque[float]] = OrderedDict()

    def allow(self, key: int) -> bool:
        now = self._clock()
        history = self._events.pop(key, deque())
        threshold = now - self.window_seconds
        while history and history[0] <= threshold:
            history.popleft()

        allowed = len(history) < self.limit
        if allowed:
            history.append(now)
        self._events[key] = history

        while len(self._events) > self.max_keys:
            self._events.popitem(last=False)
        return allowed


class SecurityMiddleware(BaseMiddleware):
    """Drops bot/group traffic and throttles user messages before handlers run."""

    def __init__(
        self,
        *,
        message_limit: int = 8,
        callback_limit: int = 15,
        window_seconds: float = 5,
        notice_window_seconds: float = 5,
    ) -> None:
        self._messages = SlidingWindowLimiter(
            limit=message_limit,
            window_seconds=window_seconds,
        )
        self._callbacks = SlidingWindowLimiter(
            limit=callback_limit,
            window_seconds=window_seconds,
        )
        self._notices = SlidingWindowLimiter(
            limit=1,
            window_seconds=notice_window_seconds,
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None and getattr(user, "is_bot", False):
            return None
        if user is None:
            return await handler(event, data)

        limiter: SlidingWindowLimiter | None = None
        if isinstance(event, Message):
            if event.chat.type != ChatType.PRIVATE:
                return None
            command = (event.text or event.caption or "").split(maxsplit=1)
            if command and command[0].split("@", 1)[0].lower() in {"/admin", "/settings"}:
                if not self._messages.allow(user.id):
                    return None
                database = data.get("db")
                is_admin = user.id in data.get("admin_ids", frozenset()) or (
                    database is not None and await database.is_admin(user.id)
                )
                if not is_admin:
                    # Hidden commands stay silent even when the sender is rate-limited.
                    return None
                return await handler(event, data)
            limiter = self._messages
        elif isinstance(event, CallbackQuery):
            message = event.message
            if not isinstance(message, Message) or message.chat.type != ChatType.PRIVATE:
                await self._notify(event, tr(user.language_code, "private_only"))
                return None
            limiter = self._callbacks

        if limiter is None or limiter.allow(user.id):
            return await handler(event, data)

        if self._notices.allow(user.id):
            await self._notify(
                event,
                tr(language_code(user.language_code), "rate_limited"),
            )
        return None

    @staticmethod
    async def _notify(event: TelegramObject, text: str) -> None:
        try:
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(text)
        except TelegramAPIError:
            logger.debug("Could not send a protection notice", exc_info=True)


@dataclass(frozen=True, slots=True)
class JobAccess:
    allowed: bool
    reason: str | None = None
    retry_after: int = 0


class RequestProtection:
    """Prevents expensive Telegram API jobs from piling up in memory."""

    def __init__(
        self,
        *,
        max_concurrent_jobs: int = 8,
        pack_cooldown_seconds: float = 8,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_concurrent_jobs < 1 or pack_cooldown_seconds < 0:
            raise ValueError("Protection values are invalid")
        self.max_concurrent_jobs = max_concurrent_jobs
        self.pack_cooldown_seconds = pack_cooldown_seconds
        self._clock = clock
        self._lock = asyncio.Lock()
        self._active_users: set[int] = set()
        self._last_pack_started: dict[int, float] = {}

    @asynccontextmanager
    async def job(self, user_id: int, *, is_pack: bool = False) -> AsyncIterator[JobAccess]:
        access = await self._reserve(user_id, is_pack=is_pack)
        try:
            yield access
        finally:
            if access.allowed:
                async with self._lock:
                    self._active_users.discard(user_id)

    @property
    def active_job_count(self) -> int:
        return len(self._active_users)

    async def _reserve(self, user_id: int, *, is_pack: bool) -> JobAccess:
        async with self._lock:
            if user_id in self._active_users:
                return JobAccess(False, "user_busy")

            now = self._clock()
            if is_pack and self.pack_cooldown_seconds:
                threshold = now - self.pack_cooldown_seconds
                self._last_pack_started = {
                    key: started
                    for key, started in self._last_pack_started.items()
                    if started > threshold
                }
                last_started = self._last_pack_started.get(user_id)
                if last_started is not None:
                    remaining = self.pack_cooldown_seconds - (now - last_started)
                    if remaining > 0:
                        return JobAccess(
                            False,
                            "pack_cooldown",
                            max(1, math.ceil(remaining)),
                        )

            if len(self._active_users) >= self.max_concurrent_jobs:
                return JobAccess(False, "capacity")

            self._active_users.add(user_id)
            if is_pack and self.pack_cooldown_seconds:
                self._last_pack_started[user_id] = now
            return JobAccess(True)
