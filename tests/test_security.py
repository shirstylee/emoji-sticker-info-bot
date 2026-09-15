from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import Chat, Message, User

from emoji_id_bot.security import (
    RequestProtection,
    SecurityMiddleware,
    SlidingWindowLimiter,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["/admin", "/admin@emoji_info_bot", "/ADMIN", "/settings"])
async def test_hidden_commands_are_silent_even_when_spammed(monkeypatch, command):
    middleware = SecurityMiddleware(message_limit=1)
    notify, handler = AsyncMock(), AsyncMock()
    monkeypatch.setattr(middleware, "_notify", notify)
    db = SimpleNamespace(is_admin=AsyncMock(return_value=False))
    event = Message(message_id=1, date=datetime.now(timezone.utc),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"), text=command)
    for _ in range(5):
        await middleware(handler, event, {"db": db, "admin_ids": frozenset({100})})
    notify.assert_not_awaited()
    handler.assert_not_awaited()
    db.is_admin.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("from_env", [True, False])
async def test_hidden_commands_reach_handlers_for_authorized_admins(from_env):
    middleware = SecurityMiddleware()
    handler = AsyncMock()
    db = SimpleNamespace(is_admin=AsyncMock(return_value=not from_env))
    event = Message(message_id=1, date=datetime.now(timezone.utc),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"), text="/admin")
    await middleware(handler, event, {"db": db, "admin_ids": frozenset({42}) if from_env else frozenset()})
    handler.assert_awaited_once()


def test_sliding_window_limiter_allows_requests_again_after_window() -> None:
    now = [100.0]
    limiter = SlidingWindowLimiter(
        limit=2,
        window_seconds=5,
        clock=lambda: now[0],
    )
    assert limiter.allow(42) is True
    assert limiter.allow(42) is True
    assert limiter.allow(42) is False
    assert limiter.allow(7) is True

    now[0] += 5
    assert limiter.allow(42) is True


@pytest.mark.asyncio
async def test_request_protection_rejects_duplicate_and_excess_jobs() -> None:
    protection = RequestProtection(max_concurrent_jobs=1)

    async with protection.job(1) as first:
        assert first.allowed is True
        async with protection.job(1) as duplicate:
            assert duplicate.reason == "user_busy"
        async with protection.job(2) as excess:
            assert excess.reason == "capacity"

    async with protection.job(2) as after_release:
        assert after_release.allowed is True


@pytest.mark.asyncio
async def test_pack_requests_have_a_cooldown() -> None:
    now = [100.0]
    protection = RequestProtection(
        pack_cooldown_seconds=8,
        clock=lambda: now[0],
    )

    async with protection.job(1, is_pack=True) as first:
        assert first.allowed is True
    async with protection.job(1, is_pack=True) as second:
        assert second.reason == "pack_cooldown"
        assert second.retry_after == 8

    now[0] += 8
    async with protection.job(1, is_pack=True) as after_cooldown:
        assert after_cooldown.allowed is True


@pytest.mark.asyncio
async def test_security_middleware_ignores_messages_from_bots() -> None:
    called = False

    async def handler(event: object, data: dict[str, object]) -> None:
        nonlocal called
        called = True

    event = SimpleNamespace(from_user=SimpleNamespace(is_bot=True))
    await SecurityMiddleware()(handler, event, {})
    assert called is False


@pytest.mark.asyncio
async def test_security_middleware_ignores_group_messages() -> None:
    called = False

    async def handler(event: object, data: dict[str, object]) -> None:
        nonlocal called
        called = True

    event = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=-100, type=ChatType.GROUP, title="Test"),
        from_user=User(id=42, is_bot=False, first_name="Test"),
        text="😀",
    )
    await SecurityMiddleware()(handler, event, {})
    assert called is False


@pytest.mark.asyncio
async def test_security_middleware_rate_limits_private_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    notices: list[str] = []

    async def handler(event: object, data: dict[str, object]) -> None:
        nonlocal calls
        calls += 1

    async def notify(event: object, text: str) -> None:
        notices.append(text)

    monkeypatch.setattr(SecurityMiddleware, "_notify", staticmethod(notify))
    middleware = SecurityMiddleware(message_limit=2, window_seconds=5)
    user = User(
        id=42,
        is_bot=False,
        first_name="Test",
        language_code="ru",
    )
    chat = Chat(id=42, type=ChatType.PRIVATE, first_name="Test")

    for message_id in range(1, 4):
        event = Message(
            message_id=message_id,
            date=datetime.now(timezone.utc),
            chat=chat,
            from_user=user,
            text="😀",
        )
        await middleware(handler, event, {})

    assert calls == 2
    assert notices == ["Слишком много действий. Подождите несколько секунд."]
