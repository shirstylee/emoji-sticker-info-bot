import asyncio

import pytest

from emoji_id_bot.main import _stop_on_windows_signal


@pytest.mark.asyncio
async def test_windows_shutdown_waits_until_polling_is_ready() -> None:
    class FakeDispatcher:
        def __init__(self) -> None:
            self.calls = 0

        async def stop_polling(self) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("Polling is not started")

    dispatcher = FakeDispatcher()
    requested = asyncio.Event()
    requested.set()
    await asyncio.wait_for(_stop_on_windows_signal(dispatcher, requested), timeout=1)
    assert dispatcher.calls == 2

